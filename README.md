# Nano-Banana (Gemini 2.5 Flash Image) Blender Add-on

BlenderからGemini 2.5 Flash Image（nano-banana）を叩くアドオン。
EDIT（単一編集）/ COMPOSE（2枚合成）対応。

## インストール

Blender の拡張機能ディレクトリに配置する際は、このリポジトリのルートフォルダ
`nano-banana-blender-addon` を `nano_banana` にリネームしてからコピーします。
フォルダ直下には `__init__.py` と `blender_manifest.toml` が存在する必要があります。

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

