# Monkey Banana (Gemini 2.5 Flash Image) Blender Add-on

## このリポジトリについて（開発終了）

**本ソフトの開発は終了しています。** 過去に制作したコードを保存し、参照・研究・改変に利用できるよう公開しています。今後の機能追加、不具合修正、セキュリティ更新は予定していません。

利用する場合は、記載された注意事項とソースコードを確認し、自己責任で使用してください。AIによる解析・改変の際も、現在保守されているソフトや、安全性を確認済みの完成品として扱わないでください。

以下の機能説明・動作環境・導入手順・開発記録は、開発当時の情報として残しています。現在のOS・外部サービス・依存ライブラリでの動作を保証するものではありません。

## 利用前にお読みください

**ソースとリスクを理解したうえで、自己責任で利用・改変してください。AIに読み込ませる場合も、この注意書きと [SECURITY.md](SECURITY.md) を必ず一緒に渡してください。**

- APIキーは `monkey_banana/monkey_banana_addon.py` のSceneプロパティ `MBProps.api_key` に保持されます。画面上の `PASSWORD` 表示は暗号化や保存除外を意味しません。
- このプロパティに `SKIP_SAVE` は指定されておらず、キーを入力して保存した `.blend` にキーが残る可能性があります。使用済みの `.blend`・バックアップ・起動用ファイルをそのまま共有しないでください。入力欄を空にしただけで過去の保存ファイルも消去されたと判断しないでください。
- 参照画像・レンダー画像・プロンプトはGoogleのAPIへ送信されます。送信できる素材だけを選び、API利用料金は利用者が確認してください。
- 配布ZIPにはREADMEが同梱されないビルド処理があります。ZIPだけを渡す場合も、この注意書きを別途添えてください。

これらは未修正の挙動です。注意書きの追加によってコードを修正したわけではありません。AI・自動化ツール向けの詳細は [AGENTS.md](AGENTS.md) と [SECURITY.md](SECURITY.md) を参照してください。


BlenderからGemini 2.5 Flash Image（monkey-banana）を叩くアドオン。
EDIT（単一編集）/ COMPOSE（2枚合成）対応。
Gemini APIの正式版エンドポイントを利用し、アスペクト比指定など最新の画像生成機能に対応しています。

## 主な機能

- Gemini 2.5 Flash Image API（正式リリース版）による画像編集/合成
- レンダリング実行からの自動アップロードと連番保存
- 参照画像を最大2枚まで利用可能
- 出力アスペクト比のプリセットおよびカスタム指定に対応

生成した画像は `mb_out_01.png`, `mb_out_02.png` のように番号を自動付与して保存され、既存ファイルを上書きしません。リミッター機能はありません。

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

