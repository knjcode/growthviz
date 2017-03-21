# growthviz

子供の写真から自動的に成長が分かるものを作る

1. 顔の位置を固定し、顔が成長していく  
   [![Demo Face](https://raw.githubusercontent.com/wiki/knjcode/growthviz/samples/mosaic_face.gif)](https://raw.githubusercontent.com/wiki/knjcode/growthviz/samples/mosaic_face.mp4)
2. 身長の大きさに合わせて、全体像で成長していく  
   [![Demo Body](https://raw.githubusercontent.com/wiki/knjcode/growthviz/samples/mosaic_body.gif)](https://raw.githubusercontent.com/wiki/knjcode/growthviz/samples/mosaic_body.mp4)

## 利用方法

ビルド済みdockerイメージを利用する方法です。

`data` ディレクトリに対象の画像を保存(現状は顔が一つだけ写った写真を想定している)した後、性別、誕生日、変換画像の最大の高さをどの身長(cm)に合わせるかの値をオプションとして以下のようにコンテナを起動します。

```
$ docker-compose run growthviz female 2011/9/18 130
```

コンテナが停止した後に、 `work` ディレクトリ配下に `face.mp4` と `body.mp4` が出力されています。

## 詳細な利用方法

自身で環境を作りたい、Google Cloud Vision APIを利用して精度を高めたい人は [詳細な利用方法](USAGE.md) を参照下さい。

## coauthor

「身長の大きさに合わせて、全体像で成長していく」および、スクリプトの一部は [ichusrlocalbin](https://github.com/ichusrlocalbin) による実装です

## ライセンス

MIT
