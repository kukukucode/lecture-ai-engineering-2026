# 第6回 解答

## 演習

- STEP 1：通常のエージェントでは search_materials、make_quiz、
  MCP経由では glossary_search_glossary が公開されることを確認した。
- STEP 2：[tool call] glossary_search_glossary({'query': '3レベル'})
- STEP 3：[tool call] fetch_fetch({'url': 'https://modelcontextprotocol.io/'})
- STEP 4：[tool call] aws_aws___search_documentation({'search_phrase': 'Amazon S3 versioning overview'})

| 接続方式 | 入力トークン | 出力トークン | モデル応答回数 |
|---|---:|---:|---:|
| 用語集 | 711 | 151 | 2 |
| fetch | 2230 | 101 | 2 |
| AWS Knowledge | 5725 | 99 | 2 |

用語集とfetchはローカルプロセスとして起動し、AWS Knowledgeは
Streamable HTTPによって外部サーバーに接続した。
コードを変更せず、設定によってツールを追加できることを確認した。

Windowsのアプリケーション制御によってuvxの実行ファイルが
ブロックされたため、セキュリティポリシーを変更せず、
署名済みPythonと独立したパッケージ環境を使用して動作を確認した。

## 宿題

取り組んだレベル：基礎・実装・発展

### 基礎

get_lecture_summaryをMCPサーバーに追加した。
サーバー側で関数を登録することで、クライアント側の
コードを変更せずに公開ツールを追加できる。

### 実装

第3回で作成したmake_quizをMCPサーバーから公開した。
存在しない講義回を指定した場合には、指定可能な講義回を返すように改善した。

TestModelを使用し、講義要約、正常なクイズ生成、
範囲外の入力（0、99）に対する応答を検証するテストを追加した。

### 発展：VS CodeのMCP設定方法の調査

調査日：2026年11月28日

VS Codeの公式ドキュメントを参照し、講義のMCP設定と
現在推奨されているCopilot向けの設定方法を比較した。

| 比較項目 | 講義のエージェント | VS Code / Copilot |
|---|---|---|
| 設定場所 | app/mcp_servers.json | ワークスペース直下の.mcp.json |
| 最上位キー | mcpServers | mcpServers |
| ローカル接続 | command、args | type: stdio、command、args |
| リモート接続 | url | type: http、url |
| 有効範囲 | 講義アプリ | ワークスペース単位またはユーザー単位 |

ユーザー単位では、COPILOT_HOME/mcp-config.json、
または既定の ~/.copilot/mcp-config.json を使用する。

#### VS Codeの設定例

```json
{
  "mcpServers": {
    "glossary": {
      "type": "stdio",
      "command": "uv",
      "args": ["run", "python", "-m", "app.mcp_server"],
      "tools": ["*"]
    },
    "aws": {
      "type": "http",
      "url": "https://knowledge-mcp.global.api.aws",
      "tools": ["*"]
    }
  }
}
```

従来のVS Codeでは .vscode/mcp.json に servers キーを
使用していたが、最新の公式資料では新規のCopilot設定に
mcpServers形式が推奨されている。
従来のLocal harnessは2027年2月に廃止予定とされている。

MCPはツールを共通のプロトコルで公開できる一方、
設定形式、起動環境、認証、承認方法はクライアントによって異なる。
そのため、接続先の信頼性と権限を確認したうえで利用する必要がある。

なお、VS CodeのCopilot経由の実行は未検証であり、
発展課題では公式資料に基づく設定方法の比較を行った。

### 参考資料

- https://code.visualstudio.com/docs/agent-customization/mcp-servers
- https://code.visualstudio.com/docs/agents/reference/mcp-configuration
- https://github.com/modelcontextprotocol/servers/tree/main/src/fetch
- https://awslabs.github.io/mcp/servers/aws-knowledge-mcp-server
