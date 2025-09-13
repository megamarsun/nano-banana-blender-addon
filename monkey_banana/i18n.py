import bpy.app.translations as tr

I18N_DICT = {
    "ja_JP": {
        ("*", "Monkey Banana (Gemini Image)"): "Monkey Banana（Gemini画像）",
        ("*", "Monkey Banana"): "Monkey Banana",
        ("*", "Gemini API Key"): "Gemini APIキー",
        ("*", "Open API Key Page"): "APIキー取得ページを開く",
        ("*", "Mode"): "モード",
        ("*", "Edit (1 image)"): "編集（1枚）",
        ("*", "Compose (Refs+Render)"): "合成（参照+レンダ）",
        ("*", "Render (Base) Image"): "レンダ（ベース）画像",
        ("*", "Ref 1 (optional)"): "参照1（任意）",
        ("*", "Ref 2 (optional)"): "参照2（任意）",
        ("*", "Edit Prompt"): "編集プロンプト",
        ("*", "Prompt Text"): "プロンプトテキスト",
        ("*", "Output Image (manual)"): "出力画像（手動）",
        ("*", "Open Result in Image Editor (manual)"): "結果をImage Editorで開く（手動）",
        ("*", "Verbose (Console + Text + File)"): "詳細ログ（コンソール + テキスト + ファイル）",
        ("*", "Last Info"): "最終情報",
        ("*", "Last Error"): "最終エラー",
        ("*", "Log Dir"): "ログフォルダ",
        ("*", "Monkey Banana Log"): "Monkey Bananaログ",
        ("*", "Run Monkey Banana (manual)"): "Monkey Bananaを実行（手動）",
        ("*", "Show Last Log"): "最後のログを表示",
        ("*", "Show Last Info"): "最終情報を表示",
        ("*", "Show Last Error"): "最終エラーを表示",
        ("*", "References (up to 2)"): "参照画像（最大2枚）",
        ("*", "Render (Base) - required"): "レンダ（ベース）- 必須",
        ("*", "Manual Run"): "手動実行",
        ("*", "Logs"): "ログ",
        ("*", "Verbose"): "詳細ログ",
        ("*", "Open in Editor"): "エディタで開く",
        ("*", "Last Info: "): "最終情報: ",
        ("*", "Last Error: "): "最終エラー: ",
        ("*", "Save path for manual run. If blank, mb_out_01.png is saved in the same folder as the render image."): "手動実行の保存先。未指定ならレンダ画像と同フォルダに mb_out_01.png 形式で保存",
    }
}


def register() -> None:
    tr.register(__name__, I18N_DICT)


def unregister() -> None:
    tr.unregister(__name__)
