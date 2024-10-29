# A Framework for Automatic Construction of scholarly Table Retrieval Test Collections
This repository hosts all relevant source code, data and resources, including LLM prompts presented in our work "A Framework for Automatic Construction of scholarly Table Retrieval Test Collections".

## Abstract
Scientific literature commonly utilizes tables to concisely present results, findings, and methodological approaches.
Tables can be a valuable relevance signal in information retrieval, yet they are rarely featured in relevance-labeled test collections.

This work presents a novel approach for automatically enriching literature collections with machine-readable parsed tables, captions, in-text references, and relevance labels for table retrieval.
As a preliminary study, we create a relevance-labeled test collection that extends a subset of the CORD-19 test collection. 

Using well-established tools and novel methods, we present an approach for table recognition and parsing of structure, captions, and content. 
Further, we employ a large language model to generate relevance labels automatically.

Building on recent findings that large language models produce document relevance judgments comparable to those of human annotators, our work suggests that this capability is transferable to assessing table relevance.

Our work provides a pipeline to facilitate the development of retrieval approaches and research focusing on tables in scientific literature.

For more details, please check the latest version of our paper: [https://...](...)

## Table of Contents

- [Repository Structure](#repository-structure)
- [Installation](#installation)
- [Additional Resources](#additional-resources)
- [License](#license)
- [Contact](#contact)

## Repository Structure

This repository is organized into several directories, each serving a specific purpose in the development and operation of the table retrieval system. Here's a breakdown of the main components:

- **`.devcontainer`**: Contains configuration files for setting up a development environment in a Docker container.

- **`data`**: This directory contains a small subset the used dataset used to test the pipeline.

- **`notebooks`**: Contains Jupyter notebooks that demonstrate the usage of the pipeline and providing examples of data processing and analysis.

- **`prompts`**: Contains prompts using GPT-4, designed for table extraction and relevance labeling, optimized for generating precise and contextually relevant table data.

- **`retrieval`**: This contains scripts and notebooks, that implement the retrieval experiment pipeline

- **`retrieval_api`**: Provides a web API for querying and retrieving scholarly articles and associated tables from a structured index.

- **`scripts`**: A collection of utility scripts used for setup, configuration, and testing of the software.

- **`src/cord19_plus`**: Source code specific to the CORD-19 test collection enhancements, including modules for downloading pdf files, processing pdfs with papermage and data models. 

- **`tests/`**: Contains tests specifically for ensuring the correctness of the code in the "src" folder

## Installation

To get started with this project, follow these steps to install the necessary dependencies:

1. Clone the repository:

   ```git clone https://github.com/...```
2. Navigate to the project directory:

   ```cd ...```
3. Install Dependencies:

   ```pip install -r requirements.txt```
4. Install Development Dependencies (Optional):

   ```pip install -r requirements_dev.txt```

These steps will ensure that all necessary Python packages are installed to run the application and develop on it. Ensure that you have Python and pip installed on your machine before beginning the installation.

## Additional Resources

For more detailed insights into our project's components, please visit the following resources:

- [Pipeline Overview](https://drive.google.com/file/d/1kG18eER45daian-PA10TJ22rmrRV4flO/view?usp=sharing): A complete overview and documentation of our used pipelines.

- [Data Model Documentation](https://drive.google.com/file/d/1N_QOc8G0_AOgNXPjCbF0w1bHhTp7GaHA/view?usp=sharing): For a deeper understanding of the data model used in this project, please see our detailed data model documentation.

## Dataset

The complete dataset is available on Zenodo and can be downloaded from there. To access and use the data for your research, please follow this link: [10.5281/zenodo.14001494](...).


## License

This project is licensed under the MIT License - see the [LICENSE](https://github.com/irgroup/CORD19_Plus/blob/main/LICENSE) file for details.

## Contact

...
