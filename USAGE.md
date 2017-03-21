# 詳細な利用方法

## セットアップ

### ローカルでdockerイメージをビルドして利用する

docker hubのイメージをpullするのではなく、ローカルでコンテナイメージをビルドしたい場合は、
以下のように `docker-compose.yml` の2行目を `build: .` に修正してください

```
growthviz:
  build: .
  container_name: "growthviz"
  volumes:
    - "$PWD/work:/app/work"
    - "$PWD/data:/app/data"
```

修正後、以下のようにコマンドを実行します

`data` ディレクトリに対象の画像を保存(現状は顔が一つだけ写った写真を想定している)した後、性別、誕生日、変換画像の最大の高さをどの身長に合わせるかの値をオプションとして以下のようにコンテナを起動します。

```
$ docker-compose run growthviz female 2011/9/18 130
```

コンテナが停止した後に、 `work` ディレクトリ配下に `face.mp4` と `body.mp4` が出力されています。

初回はコンテナのビルドがあるため多少時間がかかります。

### ローカル環境で利用する場合のセットアップ手順

macOS上で、 pyenv と pyenv-virtualenv を利用する場合の例

```
## 依存パッケージ等のインストール
$ brew update
$ brew install imagemagick ffmpeg mlt
$ brew install boost-python cmake
## pythonの仮想環境作成とpythonパッケージのインストール
## "--enable-shared" オプションを付けて python をインストールする必要があります
$ env PYTHON_CONFIGURE_OPTS="--enable-shared" pyenv install 2.7.13
$ pyenv virtualenv 2.7.13 growthviz
$ git clone git@github.com:knjcode/growthviz
$ cd growthviz
$ pyenv local growthviz
$ pip install -r requirements.txt
## dlibおよびpython-bindingのインストール
$ cd ..
$ git clone git@github.com:davisking/dlib
$ cd dlib
$ pyenv local growthviz
$ python setup.py install
$ cd ..
## dlibでの顔認識に必要なデータファイルのダウンロード
$ cd growthviz
$ wget http://dlib.net/files/shape_predictor_68_face_landmarks.dat.bz2
$ bzip2 -d shape_predictor_68_face_landmarks.dat.bz2
```

## 顔認識の動作テスト

__prepare.py__

```
$ ./prepare.py images/lenna.png
LEFT_EYE: (267.96326,267.1449)
RIGHT_EYE: (328.37363,267.3432)
degree: -0.188075528582
pupilDistance: 60.4106954639
rollAngle: 6.9850664
panAngle: 36.013985
tiltAngle: -10.279081
rotate degree: 0.188075528582
images/814a0034f5549e957ee61360d87457e5.png
```

実行後に `work/dlibcache/[画像ファイルのMD5ハッシュ]-dlib.log` という名前で顔認識結果のログをpythonのdict形式で保存します。
スクリプト実行時にログがあればそちらを優先して使います。

あわせて、両目の位置が水平になるように回転した画像を `work/face_detected` ディレクトリに出力(顔が複数ある場合は1件目に検出された顔を対象に回転)

コマンド実行時に `-c` オプションを指定した場合には、検出結果を反映した画像の生成を省略して顔認識結果のログ保存だけ行います。

## 1. 顔の位置を固定し、顔が成長していく

### 対象の画像を入れたフォルダから顔の位置を揃えた画像を生成

`/data` に対象となる画像を保存する。現状は顔が一つだけ写った写真を想定している。

また、顔が横向きであっても除外せずに結果に含めるため、極端に横を見ている画像があると不自然になると思われる。

```
$ ./face.py data
```

`work/face/affined` に処理後の画像が保存されます。

### 生成した画像から動画を作成

アニメーションGIFやmp4動画作成のために、 imagemagick および ffmpeg を利用します

mp4動画を作成 (アニメーションGIFよりサイズが小さくなります)

```
$ cp work/face/affined/* work/face/movie  # affinedディレクトリ内のファイルをmovieディレクトリにコピー
## movieディレクトリ内のファイルを movie_00001.jpg のような連番にリネームする
## macの場合はFinderで全ファイル選択後に右クリックして 「xx項目の名前を変更」 から一括リネームできます
$ ./mp4_create.sh  # work/face/movieディレクトリの連番画像からmp4動画を作成
$ open face.mp4
```

## 2. 身長の大きさに合わせて、全体像で成長していく

### 環境ファイルの修正

* `config/user.json` の `sex` に `female` か `male` を、 `birthday` に 誕生日を `YYYY/mm/dd` で記載する。

* `config/image.json` の `max_height_cm` に 変換画像の最大の高さをどの身長に合わせるかを設定する。  
  表示する身長は、 `woman_ave_height.json` もしくは `man_ave_height.json` の `height` に0歳から設定されている。女性(`woman_ave_height.json`)の場合、  
  ```
   "height": [48.4, 73.4, 84.3, 92.2, 99.5, 106.2, 112.7 ...
  ```
  と定義されており、5歳に撮った写真は `106.2` cmとして表示される。頭部分に余白を残すため、これ以上の値で、例えば、
  ```
    "max_height_cm": 120
  ```
  などと設定すればよい。

* 横長のディスプレイに表示したい場合、 `config/image.json` の `image` の `width_px`, `height_px` の値を、`landscape_example_image` の値を参考に、画像の幅、高さを設定する。

### スクリプトの実行

```
./body.py images/*.jpg
```

### 生成した画像から動画を作成

上述の 「1. 顔の位置を固定し、顔が成長していく」の「生成した画像から動画を作成」の手順で実行する。

ただし、もとのファイルは `work/body/renamed` ディレクトリに生成されるため、そのフォルダを指定する必要がある。

#### アニメーションGIFを作成

```
$ convert -layers optimize -loop 1 -delay 100 work/body/renamed/*.jpg body.gif
$ qlmanage -p body.gif  # macの場合はqlmanageコマンドでプレビューできます
```

#### (crossfade効果付き)mp4動画を作成 (アニメーションGIFよりサイズが小さくなります)

1. 動画ファイルを作成するスクリプトを実行

  ```
  $ ./create_create_video_script.py work/body/renamed/*.jpg
  ```

2. 1で作成したスクリプトを実行

  ```
  $ ./create_video.sh
  ```

`work/body.mp4` が作成される。

※ meltをbrewでインストールした場合にはうまく動かない。MacPortsでインストールすると動く

### Google Cloud Vision API を利用する

デフォルトのDlibを利用した顔認識の代わりに Google Cloud Vison の顔認識APIを利用することもできます。

#### 事前準備

始めに、Google Cloud Console にて Cloud Vision API を有効にしておきます。

次に、[Creating a service account](https://developers.google.com/identity/protocols/OAuth2ServiceAccount#creatinganaccount) 等を参考に、
Service Account key を作成し、 JSONファイルをダウンロードします。

ダウンロードしたJSONファイルのパスを `GOOGLE_APPLICATION_CREDENTIALS` 環境変数に設定します。

```
$ export GOOGLE_APPLICATION_CREDENTIALS=/path/to/service_account.json
```

#### Cloud Vision API を利用する

環境変数 `USE_GOOGLE_FACE_DETECTION` の値に "1" を設定することで、デフォルトのdlibの代わりに Cloud Vision API を利用します。

```
$ export USE_GOOGLE_FACE_DETECTION=1
```
