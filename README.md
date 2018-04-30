# slack_export

## setup 
install `pip` if you do not already have it https://pip.pypa.io/en/stable/installing/ 

install `virtualenv` 
```
pip install virtualenv
```

create your virtual environment 
```
virtualenv env 
``` 

activate the virtual environment and set `PYTHONPATH` 
```
. env/bin/activate
export PYTHONPATH=./ 
```

install required python packages into your virtualenv 
```
pip install -r reqs.txt
```

## configuration 

copy `.env.sample` to a new file named `.env` in this directory. 

fill in the following variables: 

| name | required? | description | 
| --- | --- | --- | 
| SLACK_TOKEN | yes | slack api token. generate one here: https://api.slack.com/custom-integrations/legacy-tokens | 
| CHANNEL_IDS | yes | comma-separated list of conversation IDs. ex: `G00000000,D00000000,C00000000` | 
| DIRECTORY_NAME | no | name of directory to dump files into. optional but recommended. | 
| DOWNLOAD_FILES | no | any string for yes, or leave empty (will default to not downloading) |

## run script 

```
python slack_export.py
```


