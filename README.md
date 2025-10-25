# Monkey Banana (Gemini 2.5 Flash Image) Blender Add-on

BlenderからGemini 2.5 Flash Image（monkey-banana）を叩くアドオン。
EDIT（単一編集）/ COMPOSE（2枚合成）対応。
Gemini APIの正式版エンドポイントを利用し、アスペクト比指定など最新の画像生成機能に対応しています。

## 主な機能

- Gemini 2.5 Flash Image API（正式リリース版）による画像編集/合成
- レンダリング実行からの自動アップロードと連番保存
- 参照画像を最大2枚まで利用可能
- 出力アスペクト比のプリセットおよびカスタム指定に対応

生成した画像は `mb_out_01.png`, `mb_out_02.png` のように番号を自動付与して保存され、既存ファイルを上書きしません。リミッター機能はありません。

## インストール

Blender の拡張機能ディレクトリに配置する際は、このリポジトリのルートフォルダ
`nano-banana-blender-addon` を `nano_banana` にリネームしてからコピーします。
フォルダ直下には `__init__.py` と `blender_manifest.toml` が存在する必要があります。

## Release

`python build_release.py` を実行すると、Git管理情報や `README.md` を含まない
ソースのみの `monkey_banana.zip` を生成します。バイナリやキャッシュファイルは
同梱されません。

## 開発

作業用のアドオンディレクトリは `monkey_banana/` です。VS Code の [Blender Development 拡張機能](https://marketplace.visualstudio.com/items?itemName=JacquesLucke.blender-development) を使う場合は、例えば次のように設定します。

```json
{
  "name": "Blender: Start",
  "type": "blender",
  "request": "launch",
  "path": "${workspaceFolder}/monkey_banana"
}
```

