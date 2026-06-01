import os
import streamlit as st
from google import genai
from google.genai import types
from dotenv import load_dotenv

# .envの読み込み
load_dotenv()

st.set_page_config(page_title="会話分析AIインタビュアー", layout="centered")
st.title("🎙️ 完全主導型 AI音声対話システム")
st.caption("人間の発話を高度に言語処理し、メッセージのすぐ下でリアルタイムに会話分析するAI")

# クライアント初期化
if "client" not in st.session_state:
    st.session_state.client = genai.Client()
MODEL_NAME = "gemini-2.0-flash"

# 状態（ステート）管理の初期化
if "phase" not in st.session_state:
    st.session_state.phase = "PREPARE"        
if "mbti" not in st.session_state:
    st.session_state.mbti = None
if "chat_session" not in st.session_state:
    st.session_state.chat_session = None
if "messages" not in st.session_state:
    st.session_state.messages = []
if "generated_questions" not in st.session_state:
    st.session_state.generated_questions = [
        "最近ハマっている趣味は何ですか？",
        "それを始めたきっかけを教えてください。",
        "どんな瞬間に一番楽しさを感じますか？",
        "これまでに挫折しそうになったことはありますか？",
        "今後、その趣味で挑戦してみたいことは何ですか？"
    ]  
if "current_q_index" not in st.session_state:
    st.session_state.current_q_index = 0       
if "speak_text" not in st.session_state:
    st.session_state.speak_text = None        

# テスト用のダミーメッセージ（最初からバッジが綺麗に見えるように調整）
if not st.session_state.messages:
    st.session_state.messages = [
        {
            "role": "assistant", 
            "content": "こんにちは！AIインタビュアーです。最近あなたが熱中していることについて教えてください。",
            "analysis": {"keywords": "挨拶,導入,インタビュー開始", "context": "対話の開始段階。ユーザーを歓迎している。", "aim": "ユーザーの緊張をほぐし、最初のテーマを引き出す。"}
        }
    ]

def ask_gemini_text(prompt):
    try:
        response = st.session_state.client.models.generate_content(model=MODEL_NAME, contents=prompt)
        return response.text
    except Exception as e:
        return f"エラーが発生しました。{e}"

def parse_ai_response(raw_text):
    import re
    analysis = {}
    speech = raw_text
    kw_match = re.search(r"【キーワード】[:：](.*?)(?=\n【|\Z)", raw_text, re.DOTALL)
    ctx_match = re.search(r"【文脈分析】[:：](.*?)(?=\n【|\Z)", raw_text, re.DOTALL)
    aim_match = re.search(r"【次の狙い】[:：](.*?)(?=\n【|\Z)", raw_text, re.DOTALL)
    sp_match = re.search(r"【セリフ】[:：](.*?)(?=\n【|\Z)", raw_text, re.DOTALL)
    
    if kw_match: analysis["keywords"] = kw_match.group(1).strip()
    if ctx_match: analysis["context"] = ctx_match.group(1).strip()
    if aim_match: analysis["aim"] = aim_match.group(1).strip()
    if sp_match: speech = sp_match.group(1).strip()
    else: speech = raw_text.split("【セリフ】")[-1].strip()
    return speech, analysis

# ----------------------------------------------------
# 🛠️ 開発者用・強制画面遷移メニュー（サイドバー）
# ----------------------------------------------------
with st.sidebar:
    st.markdown("## ⚙️ 開発者モード (検証用)")
    selected_phase = st.selectbox(
        "表示する画面を選択",
        options=["PREPARE", "DIAGNOSIS", "INTERVIEW_READY", "INTERVIEW", "FINISH"],
        index=["PREPARE", "DIAGNOSIS", "INTERVIEW_READY", "INTERVIEW", "FINISH"].index(st.session_state.phase),
        key="dev_phase_selector"
    )
    
    if selected_phase != st.session_state.phase:
        st.session_state.phase = selected_phase
        if selected_phase in ["INTERVIEW_READY", "INTERVIEW", "FINISH"] and not st.session_state.mbti:
            st.session_state.mbti = "ENFP"
        st.rerun()
        
    st.write("---")
    st.write("### 🏁 現在の進行ステータス")
    if st.session_state.phase == "DIAGNOSIS":
        st.info("🧠 段階1: MBTI心理診断を実行中...")
    else:
        st.success(f"🎉 診断結果: {st.session_state.mbti if st.session_state.mbti else '未確定'}")

# ----------------------------------------------------
# 📄 フェーズ1：事前準備画面
# ----------------------------------------------------
if st.session_state.phase == "PREPARE":
    st.subheader("📋 1. インタビューの方針決定")
    direction = st.text_area(
        "インタビューの目的や、ユーザーから聞き出したいこと",
        value="【目的】ユーザーが最近ハマっている趣味とその魅力について深掘りする。\n【知りたいこと】始めたきっかけ、楽しさの源泉、今後の展望",
        height=120
    )
    
    if st.button("🚀 この方針でAI対話システムを起動する", type="primary", use_container_width=True):
        st.session_state.phase = "DIAGNOSIS"
        st.rerun()

# ----------------------------------------------------
# 🎙️ フェーズ2：メイン対話画面
# ----------------------------------------------------
else:
    if st.session_state.phase == "INTERVIEW_READY":
        st.success(f"✨ MBTI診断が完了しました！あなたのタイプは 【{st.session_state.mbti}】 です。")
        if st.button("🔥 本番のディープインタビューを開始する", type="primary", use_container_width=True):
            st.session_state.phase = "INTERVIEW"
            st.rerun()

    elif st.session_state.phase == "FINISH":
        st.balloons()
        st.success("🏁 すべてのインタビュー対話が正常に終了しました！お疲れ様でした。")

    # 💬 対話タイムライン ＆ メッセージすぐ下のカラフルバッジ分析ログ
    st.subheader("💬 対話タイムライン")
    for msg in st.session_state.messages:
        with st.chat_message(msg["role"]):
            st.write(msg["content"])
            
            # 🔥 進化ポイント①：キーワードのバッジ化処理
            if msg["role"] == "assistant" and "analysis" in msg and msg["analysis"]:
                ana = msg["analysis"]
                
                # カンマ区切りのキーワードを分解して、HTMLバッジに変換
                raw_keywords = ana.get('keywords', '')
                badge_html = ""
                # 全角・半角のカンマ、読点に対応して分割
                keywords_list = [k.strip() for k in raw_keywords.replace('、', ',').replace('，', ',').split(',') if k.strip()]
                
                # スタイリッシュな青色グラデーションのバッジを動的に生成
                for kw in keywords_list:
                    badge_html += f"""
                    <span style="display: inline-block; background: linear-gradient(135deg, #3b82f6, #2563eb); color: white; padding: 2px 10px; border-radius: 12px; font-size: 0.85em; font-weight: bold; margin-right: 6px; margin-bottom: 6px; box-shadow: 0 1px 2px rgba(0,0,0,0.1);">
                        #{kw}
                    </span>
                    """
                if not badge_html:
                    badge_html = "<span style='color:#94a3b8; font-style:italic;'>なし</span>"

                # メッセージ直下の美しく装飾された分析ダッシュボード
                st.markdown(
                    f"""
                    <div style="background-color: #f8fafc; border: 1px solid #e2e8f0; border-left: 4px solid #2563eb; padding: 12px 15px; border-radius: 6px; margin-top: 10px; box-shadow: 0 1px 3px rgba(0,0,0,0.02);">
                        <div style="font-weight: bold; color: #1e293b; margin-bottom: 8px; font-size: 0.95em; display: flex; align-items: center;">
                            🛠️ AI発話分析システム
                        </div>
                        <div style="margin-bottom: 8px;">
                            <span style="color: #64748b; font-size: 0.85em; font-weight: bold; display: block; margin-bottom: 4px;">🎯 抽出キーワード</span>
                            {badge_html}
                        </div>
                        <div style="margin-bottom: 6px; font-size: 0.9em; line-height: 1.4;">
                            <span style="color: #64748b; font-size: 0.85em; font-weight: bold;">🧠 文脈分析:</span> 
                            <span style="color: #334155;">{ana.get('context', '分析中...')}</span>
                        </div>
                        <div style="font-size: 0.9em; line-height: 1.4;">
                            <span style="color: #64748b; font-size: 0.85em; font-weight: bold;">📢 次の狙い:</span> 
                            <span style="color: #334155;">{ana.get('aim', '進行管理中...')}</span>
                        </div>
                    </div>
                    """, 
                    unsafe_view_menu=False, unsafe_allow_html=True
                )

    st.write("---")

    # ─── ⌨️＋🎤 統合入力エリア（視覚エフェクト強化版） ───
    if st.session_state.phase in ["DIAGNOSIS", "INTERVIEW"]:
        st.subheader("📥 あなたの回答を伝える（声、または文字）")
        input_text = st.chat_input("ここに直接文字を入力して送信することも可能です...")

        # CSSアニメーションとリアルタイム枠線変化を仕込んだマイクUI
        js_speech_recognition = """
        <style>
        @keyframes pulse {
            0% { opacity: 0.3; }
            50% { opacity: 1; }
            100% { opacity: 0.3; }
        }
        .mic-active-dot {
            display: inline-block;
            width: 10px;
            height: 10px;
            background-color: #ef4444;
            border-radius: 50%;
            margin-right: 6px;
            animation: pulse 1.8s infinite ease-in-out;
        }
        </style>

        <div style="padding: 15px; background: #f8fafc; border: 2px solid #cbd5e1; border-radius: 10px; font-family: sans-serif;">
            <p id="mic_status" style="font-weight: bold; color: #1e293b; margin: 0 0 10px 0; font-size: 1.05em; display: flex; align-items: center;">
                <span class="mic-active-dot"></span> 🎙️ リアルタイム日本語音声認識（マイクON）
            </p>
            <div id="realtime_box" style="padding: 10px; background: white; border: 2px solid #e2e8f0; border-radius: 6px; min-height: 40px; color: #64748b; font-style: italic; font-size: 1.05em; margin-bottom: 12px; line-height: 1.4; transition: all 0.2s ease;">
                マイクに向かってお話しください。ここにあなたの言葉がリアルタイムで文字起こしされます...
            </div>
            <button id="next_submit_btn" style="width: 100%; padding: 12px; background: #2563eb; color: white; border: none; border-radius: 8px; font-size: 1.1em; font-weight: bold; cursor: pointer; box-shadow: 0 2px 4px rgba(0,0,0,0.1);">
                👉 話し終えたので、この言葉をAIに送信する
            </button>
        </div>

        <script>
        const SpeechRecognition = window.SpeechRecognition || window.webkitSpeechRecognition;
        if (!SpeechRecognition) {
            document.getElementById("mic_status").innerText = "❌ ブラウザが音声認識に非対応です。";
            document.getElementById("next_submit_btn").style.display = "none";
        } else {
            const recognition = new SpeechRecognition();
            recognition.lang = 'ja-JP'; recognition.continuous = true; recognition.interimResults = true;

            let finalTranscript = '';
            recognition.onresult = (event) => {
                let interimTranscript = '';
                for (let i = event.resultIndex; i < event.results.length; ++i) {
                    if (event.results[i].isFinal) { finalTranscript += event.results[i][0].transcript; }
                    else { interimTranscript += event.results[i][0].transcript; }
                }
                const displayArea = document.getElementById("realtime_box");
                displayArea.innerText = finalTranscript + interimTranscript;
                if(displayArea.innerText.trim() !== "") {
                    displayArea.style.borderColor = "#3b82f6";
                    displayArea.style.boxShadow = "0 0 0 3px rgba(59, 130, 246, 0.15)";
                    displayArea.style.color = "#0f172a";
                    displayArea.style.fontStyle = "normal";
                    displayArea.style.fontWeight = "500";
                }
            };
            recognition.onend = () => { recognition.start(); };

            document.getElementById("next_submit_btn").onclick = () => {
                const totalText = document.getElementById("realtime_box").innerText;
                const defaultPrompt = "マイクに向かってお話しください。";
                if(totalText && !totalText.includes(defaultPrompt) && totalText.trim() !== "") {
                    const textarea = window.parent.document.querySelector('textarea[data-testid="stChatInputTextArea"]');
                    if (textarea) {
                        let setter = Object.getOwnPropertyDescriptor(window.HTMLTextAreaElement.prototype, 'value').set;
                        setter.call(textarea, totalText);
                        textarea.dispatchEvent(new Event('input', { bubbles: true }));
                        setTimeout(() => {
                            const sendBtn = window.parent.document.querySelector('button[data-testid="stChatInputSubmitButton"]');
                            if(sendBtn) sendBtn.click();
                        }, 50);
                    }
                }
            };
            recognition.start();
        }
        </script>
        """
        st.iframe(f"data:text/html;charset=utf-8,{js_speech_recognition}", height=180)

        # 🎯 【言語処理システム（API制限対応・バッジ生成テスト可能）】
        if input_text:
            st.session_state.messages.append({"role": "user", "content": input_text})
            
            with st.spinner("🧠 AIが発話情報を高度に言語処理中..."):
                if st.session_state.chat_session:
                    if st.session_state.phase == "DIAGNOSIS":
                        prompt_msg = f"ユーザーから回答が届きました:「{input_text}」\n指定のフォーマットに沿って返答してください。"
                    else:
                        prompt_msg = f"ユーザーから回答が届きました:「{input_text}」\n指定のフォーマットに沿って高度な会話分析を返し、必要に応じて【NEXT_STAGE】を付与してください。"
                    
                    response = st.session_state.chat_session.send_message(prompt_msg)
                    raw_text = response.text
                    speech, analysis = parse_ai_response(raw_text)
                else:
                    # API制限中もバッジ機能をチェックできるよう、カンマ区切りのダミーデータを仕込む
                    speech = "（マイク・ボタン・バッジ連動チェック完了）声のデータを言語処理して、キーワードを綺麗に整列させました。"
                    analysis = {
                        "keywords": "音声認識成功, バッジ化デザイン, 最高のUI体験", 
                        "context": "ユーザーが話し終えてボタンを押したことで、システムプログラミングが正常にバッジを生成した。", 
                        "aim": "これで①と②の機能とデザインが完全一致しました！明日からの実験が楽しみですね。"
                    }
                
                st.session_state.speak_text = speech  
                st.session_state.messages.append({"role": "assistant", "content": speech, "analysis": analysis})
            st.rerun()

    # ─── 🔊 AI発話システム ───
    if st.session_state.speak_text and st.session_state.chat_session:
        safe_text = st.session_state.speak_text.replace("'", "\\'").replace("\n", " ")
        js_speech = f"""
        <script>
            const uttr = new SpeechSynthesisUtterance('{safe_text}');
            uttr.lang = 'ja-JP'; uttr.rate = 1.1;
            window.speechSynthesis.speak(uttr);
        </script>
        """
        st.iframe(f"data:text/html;charset=utf-8,{js_speech}", height=1)
        st.session_state.speak_text = None 
        st.rerun()