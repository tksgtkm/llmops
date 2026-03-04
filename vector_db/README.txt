データセットの手に入れ方(数十分かかるかも！)
git clone https://github.com/amazon-science/esci-data.git


docker compose 起動
docker composeup --build
docker compose up --detach

pythonファイル実行
docker compose exec workspace python /code/data_preparation.py

docker compose 終了
docker compose down