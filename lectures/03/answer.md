# 第3回 解答

## 演習

- 第1回（素のLLM）とエージェントの回答の違い：
  第1回の素のLLMは外部の講座用語集を参照しない。一方、第3回のエージェントは、lecNN-startタグについてsearch_glossaryを呼び出し、取得した定義に沿って正しく回答できた。講座固有の情報を確認してから回答する点が大きな違いだと分かった。

- `--trace` で見えたツール呼び出し（ツール名と引数）：
  lecNN-startタグの質問ではsearch_glossary(query="lecNN-start タグ")が1回呼ばれた。LoRAとQLoRAの比較では、search_glossary(query="LoRA")とsearch_glossary(query="QLoRA")がそれぞれ呼ばれた。

- 1つの質問での LLM 呼び出し回数（`requests`）：
  lecNN-startタグの質問は2回、LoRAとQLoRAの比較も2回だった。後者では1回の質問で2つのツール呼び出しが記録された。

- 追加したツールと、docstring に書いた説明：
  make_quiz(lecture: int)を追加した。指定された講義回の用語からランダムに1語を選び、確認問題と模範解答を返す。docstringには、利用者が講義内容を復習したい場合に使用すること、最初は問題だけを提示することを記載した。存在しない回にはエラーメッセージを返す。専用テストを3件追加し、既存テストと合わせて14件が成功した。

## 宿題

- 取り組んだレベル：発展（a：Google ADKで再実装）

- やったこと：
  Google ADK版の学習支援エージェントをadk_lecture_agent/agent.pyに実装した。Pydantic AI版と同じGeminiモデル、INSTRUCTIONS、およびsearch_glossary、get_lecture_summary、make_quizの3つのツールを使用した。ADK CLIで3種類の質問を試し、さらにInMemoryRunnerを利用するスクリプトを作成して、ツール呼び出しと実行結果を記録した。adk webの起動も試した。

- 結果：
  ADK CLIではlecNN-startタグとLoRA・QLoRAの説明を正しく生成した。確認問題の質問では、最初のCLI実行時に問題文が表示されなかったが、InMemoryRunnerによる再実行ではmake_quiz(lecture=2)の呼び出しと結果の返却を確認できた。実際に「量子化とは何ですか？」という問題が生成され、最終回答でも模範解答を伏せて出題できた。

  Pydantic AIではagent.tool_plain()でツールを登録し、--traceでツール呼び出し・引数・使用量を表示する。一方、Google ADKではAgentのtoolsリストに関数を指定し、Runnerから取得したイベントのfunction_callsとfunction_responsesを調べた。

  adk webのサーバー起動には成功したものの、Codespacesの転送URL経由ではJavaScriptファイルへのアクセスがHTTP 403となり、Web UIの画面表示や操作性の比較は実施できなかった。Codespaces内部から同じファイルへアクセスした場合はHTTP 200であり、原因は未確定である。

- 気づき・疑問：
  どちらのフレームワークでもモデル・指示文・ツールを組み合わせてエージェントを構築できたが、ツール登録方法と実行履歴の取得方法が異なった。また、ツールが正しく結果を返しても、利用者向けの最終回答が常に期待どおりになるとは限らない。ツール実行と最終回答を分けて検証することが重要だと学んだ。
