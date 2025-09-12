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
        ("*", "Prompt Text"): "プロンプトテキスト",
        ("*", "New Prompt Text"): "新規プロンプトテキスト",
        ("*", "Output Image (manual)"): "出力画像（手動）",
        ("*", "Open Result in Image Editor (manual)"): "結果をImage Editorで開く（手動）",
        ("*", "Verbose (Console + Text + File)"): "詳細ログ（コンソール + テキスト + ファイル）",
        ("*", "Last Info"): "最終情報",
        ("*", "Last Error"): "最終エラー",
        ("*", "Log Dir"): "ログフォルダ",
        ("*", "Nano-Banana Log"): "Nano-Bananaログ",
        ("*", "Run nano-banana (manual)"): "nano-bananaを実行（手動）",
        ("*", "Show Last Log"): "最後のログを表示",
        ("*", "Show Last Info"): "最終情報を表示",
        ("*", "Show Last Error"): "最終エラーを表示",
        ("*", "References (up to 2)"): "参照画像（最大2枚）",
        ("*", "Render (Base) - required"): "レンダ（ベース）- 必須",
        ("*", "Manual Run"): "手動実行",
        ("*", "Logs"): "ログ",
        ("*", "Verbose"): "詳細ログ",
        ("*", "Last Info: "): "最終情報: ",
        ("*", "Last Error: "): "最終エラー: ",
        ("*", "Save path for manual run. If blank, nb_out_01.png is saved in the same folder as the render image."): "手動実行の保存先。未指定ならレンダ画像と同フォルダに nb_out_01.png 形式で保存",
    }
}


def register() -> None:
    tr.register(__name__, I18N_DICT)


def unregister() -> None:
    tr.unregister(__name__)
