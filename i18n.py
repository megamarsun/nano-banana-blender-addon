import bpy.app.translations as tr

I18N_DICT = {
    "ja_JP": {
        ("*", "Nano-Banana (Gemini Image)"): "Nano-Banana（Gemini画像）",
        ("*", "Nano-Banana"): "Nano-Banana",
        ("*", "Gemini API Key"): "Gemini APIキー",
        ("*", "Mode"): "モード",
        ("*", "Edit (1 image)"): "編集（1枚）",
        ("*", "Compose (Refs+Render)"): "合成（参照+レンダ）",
        ("*", "Render (Base) Image"): "レンダ（ベース）画像",
        ("*", "Ref 1 (optional)"): "参照1（任意）",
        ("*", "Ref 2 (optional)"): "参照2（任意）",
        ("*", "Edit Prompt"): "編集プロンプト",
        ("*", "Output Image (manual)"): "出力画像（手動）",
        ("*", "Open Result in Image Editor (manual)"): "結果をImage Editorで開く（手動）",
        ("*", "Auto Run on Render"): "レンダ時に自動実行",
        ("*", "Auto Output Dir"): "自動出力フォルダ",
        ("*", "Use Limiter"): "リミッター使用",
        ("*", "Max Calls"): "最大回数",
        ("*", "Used"): "使用数",
        ("*", "Verbose (Console + Text + File)"): "詳細ログ（コンソール + テキスト + ファイル）",
        ("*", "Last Info"): "最終情報",
        ("*", "Last Error"): "最終エラー",
        ("*", "Log Dir"): "ログフォルダ",
        ("*", "Nano-Banana Log"): "Nano-Bananaログ",
        ("*", "Run nano-banana (manual)"): "nano-bananaを実行（手動）",
        ("*", "Apply Auto Run on Render"): "レンダ自動実行を適用",
        ("*", "Reset Limiter Counter"): "リミッターカウンタをリセット",
        ("*", "Show Last Log"): "最後のログを表示",
        ("*", "Show Last Info"): "最終情報を表示",
        ("*", "Show Last Error"): "最終エラーを表示",
        ("*", "References (up to 2)"): "参照画像（最大2枚）",
        ("*", "Render (Base) - required"): "レンダ（ベース）- 必須",
        ("*", "Manual Run"): "手動実行",
        ("*", "Auto Run on Render (per-frame)"): "レンダごとに自動実行",
        ("*", "Enabled"): "有効",
        ("*", "Apply"): "適用",
        ("*", "Limiter"): "リミッター",
        ("*", "Logs"): "ログ",
        ("*", "Verbose"): "詳細ログ",
        ("*", "Last Info: "): "最終情報: ",
        ("*", "Last Error: "): "最終エラー: ",
    }
}


def register() -> None:
    tr.register(__name__, I18N_DICT)


def unregister() -> None:
    tr.unregister(__name__)
