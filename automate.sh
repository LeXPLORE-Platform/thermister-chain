cd /home/jamesr/lake-murten-mooring

/home/jamesr/.pyenv/versions/pylake/bin/python scripts/main.py live

/home/jamesr/.pyenv/versions/pylake/bin/python scripts/upload_remote_data.py -d -w

curl "https://api.datalakes-eawag.ch/update/956"
curl "https://api.datalakes-eawag.ch/update/1221"
