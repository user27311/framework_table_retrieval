import logging

import autoqrels.zeroshot
import tiktoken
from ir_datasets import Dataset
from openai import OpenAI
import base64
import requests
import cv2
from pathlib import Path
from typing import Union
import json
import tqdm

import autoqrels

logger = logging.getLogger(__name__)


class GPT(autoqrels.zeroshot.ZeroShotLabeler):
    def __init__(
        self,
        dataset: Dataset,
        api_key: str,
        model_name: str,
        prompt: bool = None,
        query_field: str = None,
        doc_field: str = None,
    ) -> None:
        super().__init__()
        self._openai_client = OpenAI(api_key=api_key)
        self.dataset = dataset
        self.model = model_name
        self.query_field = query_field
        self.doc_field = doc_field

        if prompt:
            self.prompt = prompt
        else:
            self.prompt = f"""Instruction: Indicate if the document is relevant to the query. Only answer with 0, 1, 2 where 0 is the lowest grade and 2 the highest. Query: QUERY_TEXT, Document: UNK_DOC_TEXT, Relevant: """

    def _infer_zeroshot(self, query_id: str, unk_doc_ids: list[str]):
        return self._infer_zeroshot_text(
            autoqrels.text.query_text(self.dataset, [query_id], self.query_field),
            autoqrels.text.doc_text(self.dataset, unk_doc_ids, self.doc_field),
        )

    def _infer_zeroshot_text(self, query_text: list[str], unk_doc_texts: list[str]) -> list[float]:
        results = []
        for unk_doc_text in tqdm.tqdm(unk_doc_texts):
            prompt = self.prompt.replace("QUERY_TEXT", query_text[0]).replace("UNK_DOC_TEXT", unk_doc_text)
            completion = self._openai_client.chat.completions.create(
                model=self.model, messages=[{"role": "user", "content": prompt}]
            )
            results.append(completion.choices[0].message.content)
        return results

    def estimate_price(
        self,
        table_json,
        in_token_price=0.150 / 1_000_000,
        out_token_price=0.600 / 1_000_000,
        output_text="Irrelevant",
    ):

        enc = tiktoken.encoding_for_model(self.model)
        p_enc = enc.encode(self.prompt.replace("TABLE_JSON", str(table_json)))

        price_input = len(p_enc) * in_token_price
        price_output = len(enc.encode(output_text)) * out_token_price
        return price_input + price_output


class GPTVision(autoqrels.zeroshot.ZeroShotLabeler):
    def __init__(self, dataset: Dataset, api_key: str, model_name: str, prompt: bool = None, query_field=None) -> None:
        super().__init__()
        self._api_key = api_key
        self._openai_client = OpenAI(api_key=self._api_key)
        self.dataset = dataset
        self.model = model_name
        self.query_field = query_field
        if prompt:
            self.prompt = prompt
        else:
            self.prompt = f"""Instruction: Indicate if the document is relevant to the query. Only answer with 0, 1, 2 where 0 is the lowest grade and 2 the highest. Query: QUERY_TEXT, Relevant: """

    def _infer_zeroshot(self, query_id: str, unk_doc_paths: list[Union[str, Path]]):
        return self._infer_zeroshot_image(
            autoqrels.text.query_text(self.dataset, [query_id], self.query_field), unk_doc_paths
        )

    def _infer_zeroshot_image(self, query_text: list[str], unk_doc_paths: list[Union[str, Path]]) -> list[float]:
        results = []
        for unk_doc_path in unk_doc_paths:
            prompt = self.prompt.replace("QUERY_TEXT", query_text[0])
            enc_image = self._encode_image(unk_doc_path)
            headers = {"Content-Type": "application/json", "Authorization": f"Bearer {self._api_key}"}
            payload = {
                "model": self.model,
                "messages": [
                    {
                        "role": "user",
                        "content": [
                            {"type": "text", "text": prompt},
                            {"type": "image_url", "image_url": {"url": f"data:image/jpeg;base64,{enc_image}"}},
                        ],
                    }
                ],
                "max_tokens": 20,
            }
            response = requests.post("https://api.openai.com/v1/chat/completions", headers=headers, json=payload)
            results.append(response.json()["choices"][0]["message"]["content"])
        return results

    def _encode_image(self, image_path: Union[str, Path]):
        with open(image_path, "rb") as image_file:
            return base64.b64encode(image_file.read()).decode("utf-8")

    def estimate_price(
        self,
        table_image_path,
        in_token_price=0.150 / 1_000_000,
        out_token_price=0.600 / 1_000_000,
        tile_tokens=5667,
        base_tokens=2833,
        output_text="Highly Relevant",
        image_only=False,
    ):
        im = cv2.imread(table_image_path)
        x, y, _ = im.shape

        if any([side > 2048 for side in (x, y)]):
            if x > y:
                y_scale = 2048 / x
                x = 2048
                y = y * y_scale
            elif y > x:
                x_scale = 2048 / y
                y = 2048
                x = x * x_scale

        if x > y:
            y_scale = 768 / x
            x = 768
            y = y * y_scale

        elif y > x:
            x_scale = 768 / y
            y = 768
            x = x * x_scale

        if x % 512 == 0:
            tiles_x = int(x / 512)
        else:
            tiles_x = x // 512 + 1

        if y % 512 == 0:
            tiles_y = int(y / 512)
        else:
            tiles_y = y // 512 + 1

        if any([side > 2048 for side in (x, y)]):
            raise NotImplementedError(
                "Resizing calculations do not work for this image. Its ratio is probably very skewed."
            )

        n_tiles = tiles_x * tiles_y
        tokens = base_tokens + (n_tiles * tile_tokens)
        enc = tiktoken.encoding_for_model(self.model)

        if image_only:
            price_input = (tokens) * in_token_price
            price_output = len(enc.encode("Irrelevant")) * out_token_price
            return price_input + price_output
        else:
            p_enc = enc.encode(self.prompt)
            price_input = (len(p_enc) + tokens) * in_token_price
            price_output = len(enc.encode("Irrelevant")) * out_token_price
            return price_input + price_output
