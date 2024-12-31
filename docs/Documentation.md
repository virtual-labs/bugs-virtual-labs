# This document summarizes the entire bug filter code and scripts used for the same.

## The filter logic
- The filter resides as a github workflow in the workflows of this repository. The `filter.yml` file can be triggered to run a github action which sequentially calls a python script in `src` directory named `run_filter.py`. This script required two environment variables; namely 'REPO_ACCESS_TOKEN' and 'GOOGLE_API_KEY'. 
- This filter fetches the oldest 12 'Unprocessed issues' from the `virtual-labs/bugs-virtual-labs` repository by sending HTTP requests using the GitHub API. This requires valid token keys so ensure that the keys have no expiration date or are modified in the environment periodically so that the filter doesn't stop working.
- We prompt the LLM to label the given user comment as NSFW (Not safe for work) or SFW. For this we extract the body of the github issue and parse the "Additional info-" field manually. This is done by reading all lines till the line containing "User Agent", a guaranteed field in the body. This method is a little inefficient and prone to failing in complicated scenarios (however they are unlikely to arise). A JSON object of the issue can be utilised in the future to make things easier.
- After finding inappropriate issues in the batch of 12, we remove the unprocessed tags for all so that the LLM never picks them up again for the task, ensuring that each issue gets processed only once.

## The workflow

- The github workflow for the same is set to be triggered everytime an issue is logged and periodically say every 2 hours. The configuration can be changed.

## Testing the filter.

- The code to test the filter resides in the `test` directory. It is not required after deploying the filter but remains as a proof of the evaluation carried out on the feature before it's integration.
- We first download all issues into a csv file (This is done by backing up all issues in a google sheet maintained by VLabs which will be mentioned later on).
- The `issues.csv` is used to run `csv_test.py` which passes all issues in the csv to the LLM and generates classification results and creates a checkpoint file called `checkpoint.pkl`. Even if the script stops midway, you can resume from where you left since the checkpoint is always changed. 
- The `predict.py` uses the `checkpoint.pkl` to generate classification metrics (true positives, false positives and false negatives).
- The `fetch.py` is a hardcoded script used to find out more on what issues were actually labelled as what. It creates three json files, each storing the entire metadata of all issues classified as TN, FP or FN.
- Sequentially one runs `csv_test.py` with the help of `issues.csv` which generates `checkpoint.pkl` and using this generated file one runs `predict.py`. Using the issue numbers printed by `predict.py` we run the `fetch.py` to generate reports of all TP,FP and FN.

## Backing up issues
- Another side project was to continuously back up all recorded issues in a google sheets maintained by VLabs. Sheet link <a href='https://docs.google.com/spreadsheets/d/1EfS5lIMw8mjVzGLKbZVLZRr1bY_r4TPxTt7bui1mr58/edit?gid=0#gid=0'>here.</a> 
- An Appscript code was written for the sheet which uses the github API to read all issues and write them into the excel. Code <a href='https://script.google.com/u/0/home/projects/1ZhA1GjJx4I38NxWegTnT6eSKfxodJwbcWdRwvjCuVFWXpPxsko3jLhUM/edit'>here.</a>
- It is triggered periodically (once everyday).
- The API key and other details are stored in the Scripts property of the Appscript code. Ensure that the keys are properly set.


    