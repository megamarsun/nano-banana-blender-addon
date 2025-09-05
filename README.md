# Nano-Banana (Gemini 2.5 Flash Image) Blender Add-on

BlenderからGemini 2.5 Flash Image（nano-banana）を叩くアドオン。
EDIT（単一編集）/ COMPOSE（2枚合成）対応。

## Release

Blender 4.3以降のエクステンションとして、このリポジトリ直下をZip化してインストールできます。

## 開発

作業用のアドオンディレクトリはリポジトリ直下です。VS Code の [Blender Development 拡張機能](https://marketplace.visualstudio.com/items?itemName=JacquesLucke.blender-development) を使う場合は、例えば次のように設定します。

```json
{
  "name": "Blender: Start",
  "type": "blender",
  "request": "launch",
  "path": "${workspaceFolder}"
}
```

