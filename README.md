# 概要
GCP上で定期的に[SRSグループ](https://srs-holdings.co.jp/ir/library/monthly/)のWebサイトから月次の売上情報をBeautifulSoupを利用してスクレイピングし、データベースに保存する仕組みを作成しました。

# 環境
- Python3.7  
- Beautiful Soup  
- Cloud Scheduler  
スクレイピングを定期実行するために、Pub/Subにメッセージを送信。  
- Cloud Pub/Sub  
- Cloud Functions  
- Cloud SQL  
データベースにはMySQLを指定。

# 構成
![SRSグループスクレイピング_GCP](https://user-images.githubusercontent.com/18655253/74220572-52509c80-4cf3-11ea-80ae-3facebf5e259.png)
1. 事前準備(pubsubトピック作成、Cloud SQL Database/Table作成)
2. Cloud SchedulerからCloud Functionsをトリガーするために、定期的にCLoud Pub/Subにメッセージ送信
3. Pub/Sub経由でFunctionsを実行
4. Functionsで、BeautifulSoup4を利用してSRSグループのウェブサイトをスクレイピング
5. FunctionsからCloud SQLへデータをインサート

# テーブル設計
以下、Cloud SQLに作成したテーブルの情報となります。
| カラム名 | 型 | その他 |
----|----|----
| restaurantID | INT | NOT NULL AUTO_INCREMENT PRIMARY KEY|
| companyName | VARCHAR(255) | |
| isGroup | BOOLEAN | |
| restaurantName | VARCHAR(255) | |
| YM | VARCHAR(255) | |
| salesPercent | FLOAT | |
| customerNumPercent | FLOAT | |
| avgSpendPercent | FLOAT | |
| createdAt | TIMESTAMP | |

# スクレイピングする情報
以下、[Webサイト](https://srs-holdings.co.jp/ir/library/monthly/)からスクレイピングする情報となります。
<img width="646" alt="2020-02-11_18h10_29" src="https://user-images.githubusercontent.com/18655253/74225147-7a44fd80-4cfd-11ea-8461-fd1a5c67fba1.png">
