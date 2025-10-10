# Monkey Banana (Gemini 2.5 Flash Image) Blender Add-on

BlenderからGemini 2.5 Flash Image（monkey-banana）を叩くアドオン。
EDIT（単一編集）/ COMPOSE（2枚合成）対応。

生成した画像は `mb_out_01.png`, `mb_out_02.png` のように番号を自動付与して保存され、既存ファイルを上書きしません。リミッター機能はありません。

## Release

`python build_release.py` を実行すると、Git管理情報や `README.md` を含まない
ソースのみの `monkey_banana.zip` を生成します。バイナリやキャッシュファイルは
同梱されません。

## GitHub 429 対策メモ

GitHub への匿名HTTPSアクセスでは、フェッチやクローン時に **HTTP 429 (Too Many Requests)** が
発生することがあります。以下のいずれかで認証済みアクセスへ切り替えるとレート制限を
回避しやすくなります。

### 1. HTTPS + Git Credential Manager を利用する場合

```bash
git config --global credential.helper manager-core
git credential-manager-core erase https://github.com
git fetch origin codex/update-monkey-banana-api/ux-specifications --force
git switch -C codex/update-monkey-banana-api/ux-specifications origin/codex/update-monkey-banana-api/ux-specifications
git reset --hard origin/codex/update-monkey-banana-api/ux-specifications
```

### 2. SSH へ切り替える場合

```bash
ssh-keygen -t ed25519 -C "your_email@example.com" -f ~/.ssh/id_ed25519 -N ""
eval "$(ssh-agent -s)"
ssh-add ~/.ssh/id_ed25519
# 公開鍵(~/.ssh/id_ed25519.pub)を GitHub の "SSH and GPG keys" に登録
git remote set-url origin git@github.com:megamarsun/nano-banana-blender-addon.git
git fetch origin codex/update-monkey-banana-api/ux-specifications --force
git switch -C codex/update-monkey-banana-api/ux-specifications origin/codex/update-monkey-banana-api/ux-specifications
git reset --hard origin/codex/update-monkey-banana-api/ux-specifications
```

ネットワーク制限が厳しい場合は `GIT_CURL_VERBOSE=1` を指定して詳細ログを確認し、組織内プロキシや
VPN 設定を見直してください。

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

