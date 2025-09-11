# Nano-Banana (Gemini 2.5 Flash Image) Blender Add-on

BlenderからGemini 2.5 Flash Image（nano-banana）を叩くアドオン。
EDIT（単一編集）/ COMPOSE（2枚合成）対応。

生成した画像は `nb_out_01.png`, `nb_out_02.png` のように番号を自動付与して保存され、既存ファイルを上書きしません。リミッター機能はありません。

## Release

`python build_release.py` を実行すると、Git管理情報や `README.md` を含まない
ソースのみの `nano_banana.zip` を生成します。バイナリやキャッシュファイルは
同梱されません。

## 開発

作業用のアドオンディレクトリは `nano_banana/` です。VS Code の [Blender Development 拡張機能](https://marketplace.visualstudio.com/items?itemName=JacquesLucke.blender-development) を使う場合は、例えば次のように設定します。

```json
{
  "name": "Blender: Start",
  "type": "blender",
  "request": "launch",
  "path": "${workspaceFolder}/nano_banana"
}
```

