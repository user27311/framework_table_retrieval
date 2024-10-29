# Download scripts are broken due to changes in Index
## Trec covid

### Using the Dockerfiles

To use the Dockerfiles move them into the root of this git repo, then run these commands:
- Build: docker build -t trec-covid-openalex -f Dockerfile.openalex
- Run: docker run --name trec-covid-openalex -d --mount src=/CORD19+/,destination=/CORD19+/,type=bind trec-covid-openalex

For running the pdfs container just replace openalex with pdfs for all occasions.