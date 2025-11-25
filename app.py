import streamlit as st
import pandas as pd
import numpy as np
from pipeline.pipeline import LoanAIPipeline
from utils.db import (
    get_account,
    list_transactions,
)

# ----------------------------------------------------
# Session State 保護（防止 tab 切換資料消失）
# ----------------------------------------------------
session_defaults = {
    "kyc_data": None,
    "features": None,
    "pd": None,
    "decision": None,
    "limit": None,
    "user_id": None,
}
for key, val in session_defaults.items():
    if key not in st.session_state:
        st.session_state[key] = val

# ----------------------------------------------------
# UI 設定
# ----------------------------------------------------
st.set_page_config(page_title="Loan AI Approval System", page_icon="💼", layout="wide")

PRIMARY_BLUE = "#1A73E8"

st.markdown(f"""
<style>
.main {{
    background-color: #FFFFFF;
    font-family: 'Segoe UI', sans-serif;
}}
.title {{
    font-size: 32px;
    font-weight: 700;
    color: {PRIMARY_BLUE};
    padding-bottom: 10px;
}}
.sub {{
    font-size: 20px;
    font-weight: 600;
    color: #333333;
}}
</style>
""", unsafe_allow_html=True)

pipeline = LoanAIPipeline()

st.markdown("<div class='title'>AI 貸款審件系統（Loan Approval + Revolving Credit Demo）</div>", unsafe_allow_html=True)

tabs = st.tabs([
    "📝 KYC 填寫",
    "🤖 AI 模型",
    "📘 審件決策",
    "🧾 建立客戶帳戶",
    "💰 借款 / 還款",
    "📊 Dashboard"
])

# ====================================================
# Tab 1 — KYC
# ====================================================
with tabs[0]:
    st.markdown("<div class='sub'>Step 1：KYC 基本資料</div>", unsafe_allow_html=True)

    with st.form("kyc_form"):
        # 設置 key 以便記憶輸入值
        name = st.text_input("姓名", value=st.session_state["kyc_data"].get("name", "") if st.session_state["kyc_data"] else "", key="kyc_name")
        nid_last4 = st.text_input("身分證後四碼", value=st.session_state["kyc_data"].get("national_id_last4", "") if st.session_state["kyc_data"] else "", key="kyc_nid")
        age = st.number_input("年齡", min_value=18, max_value=80, value=st.session_state["kyc_data"].get("age", 30) if st.session_state["kyc_data"] else 30, key="kyc_age")
        income = st.number_input("月收入（NTD）", min_value=0, value=st.session_state["kyc_data"].get("income", 40000) if st.session_state["kyc_data"] else 40000, key="kyc_income")
        job = st.selectbox("工作類型", ["上班族", "學生", "自營業", "無業", "其他"], index=["上班族", "學生", "自營業", "無業", "其他"].index(st.session_state["kyc_data"].get("job_type", "上班族")) if st.session_state["kyc_data"] else 0, key="kyc_job")
        region = st.selectbox("居住地區", ["北部", "中部", "南部", "東部", "外島"], index=["北部", "中部", "南部", "東部", "外島"].index(st.session_state["kyc_data"].get("region", "北部")) if st.session_state["kyc_data"] else 0, key="kyc_region")

        submitted = st.form_submit_button("送出 KYC")

    if submitted:
        # 清空所有後續步驟的計算結果 (確保重新計算)
        st.session_state["features"] = None
        st.session_state["pd"] = None
        st.session_state["decision"] = None
        st.session_state["limit"] = None
        
        # 儲存新的 KYC 資料
        st.session_state["kyc_data"] = {
            "name": name,
            "national_id_last4": nid_last4,
            "age": age,
            "income": income,
            "job_type": job,
            "region": region
        }
        st.success("KYC 已送出 ✔ 請前往下一步")

# ====================================================
# Tab 2 — AI PD
# ====================================================
with tabs[1]:
    st.markdown("<div class='sub'>Step 2：AI PD 模型評估</div>", unsafe_allow_html=True)

    if st.session_state["kyc_data"] is None:
        st.warning("請先完成 Step 1：KYC")
    else:
        # 僅在 PD 尚未計算時才執行
        if st.session_state["pd"] is None:
            features = pipeline.process_kyc(st.session_state["kyc_data"])
            pd_value = pipeline.calculate_pd(features)

            st.session_state["features"] = features
            st.session_state["pd"] = pd_value
        
        # 顯示結果
        pd_value = st.session_state["pd"]
        features = st.session_state["features"]

        col1, col2 = st.columns(2)
        with col1:
            st.metric("違約機率（PD）", f"{pd_value:.2%}")
        with col2:
            st.json(features)

# ====================================================
# Tab 3 — Decision Engine
# ====================================================
with tabs[2]:
    st.markdown("<div class='sub'>Step 3：AI 審件決策</div>", unsafe_allow_html=True)

    if st.session_state["pd"] is None:
        st.warning("請先至 Step 2：AI PD 模型")
    else:
        # 僅在 Decision 尚未計算時才執行
        if st.session_state["decision"] is None:
            pd_value = st.session_state["pd"]
            decision = pipeline.decision(pd_value)
            limit = pipeline.calculate_limit(pd_value)

            st.session_state["decision"] = decision
            st.session_state["limit"] = limit
        
        # 顯示結果
        decision = st.session_state["decision"]
        limit = st.session_state["limit"]

        if decision == "reject":
            st.error("❌ 審件結果：拒絕")
        elif decision == "review":
            st.warning("⚠️ 審件結果：人工審核 / 補件")
        else:
            st.success("✔ 審件結果：核准")

        st.metric("核准額度（NTD）", f"{limit:,}")

# ====================================================
# Tab 4 — 建立帳戶
# ====================================================
with tabs[3]:
    st.markdown("<div class='sub'>Step 4：建立客戶帳戶（寫入 DB）</div>", unsafe_allow_html=True)

    if st.session_state["decision"] != "approve":
        st.warning("需先完成審件並核准才可建立帳戶")
    else:
        # 只有在尚未建立 user_id 且已核准時才顯示建立按鈕
        if st.session_state["user_id"] is None:
            if st.button("建立帳戶"):
                # 執行建檔
                user_id = pipeline.create_user(
                    st.session_state["kyc_data"],
                    st.session_state["pd"],
                    st.session_state["limit"]
                )
                st.session_state["user_id"] = user_id
                st.success(f"帳戶建立成功！User ID：{user_id}")
                st.experimental_rerun() # 建檔成功後強制重跑一次以顯示最新狀態

        if st.session_state["user_id"] is not None:
            st.success(f"帳戶已存在！User ID：{st.session_state['user_id']}")
            # 可以顯示帳戶基本資訊
            acct = get_account(st.session_state["user_id"])
            if acct:
                 st.write(f"總額度：NTD {acct['limit_amount']:,}")
                 st.write(f"起始可用額度：NTD {acct['available_credit']:,}")


# ====================================================
# Tab 5 — 借款 / 還款
# ====================================================
with tabs[4]:
    st.markdown("<div class='sub'>Step 5：隨借隨還（Revolving Credit）</div>", unsafe_allow_html=True)

    if st.session_state["user_id"] is None:
        st.warning("請先建立帳戶")
    else:
        user_id = st.session_state["user_id"]

        # ★ 永遠讀取最新狀態
        acct = get_account(user_id)

        st.write(f"**用戶：{user_id}**")

        st.metric("可用額度", f"{acct['available_credit']:,}")
        st.metric("欠款餘額", f"{acct['outstanding_balance']:,}")

        # ★ 手動重新整理
        if st.button("🔄 重新整理資料"):
            st.experimental_rerun()

        st.divider()

        # 借款
        borrow_amount = st.number_input("借款金額", min_value=0, value=5000, key="borrow_amount")
        if st.button("借款"):
            resp = pipeline.borrow(user_id, borrow_amount)
            if resp["success"]:
                st.success(f"借款成功！新的餘額：{resp['after_balance']:,}")
                st.experimental_rerun()
            else:
                st.error(resp["msg"])

        st.divider()

        # 還款
        repay_amount = st.number_input("還款金額", min_value=0, value=3000, key="repay_amount")
        if st.button("還款"):
            resp = pipeline.repay(user_id, repay_amount)
            if resp["success"]:
                st.success(f"還款成功！新的餘額：{resp['after_balance']:,}")
                st.experimental_rerun()
            else:
                st.error(resp["msg"])

        st.divider()

        # 交易紀錄
        st.subheader("📜 交易紀錄（最新）")
        df_trans_rows = list_transactions(user_id) # 這裡會回傳 tuple list
        
        if len(df_trans_rows) == 0:
            st.info("目前沒有借款/還款紀錄")
        else:
            # 轉換為 DataFrame
            df_trans = pd.DataFrame(df_trans_rows, columns=["type", "amount", "timestamp"])
            st.dataframe(df_trans, use_container_width=True)

# ====================================================
# Tab 6 — Dashboard
# ====================================================
with tabs[5]:
    st.markdown("<div class='sub'>Step 6：Dashboard（交易紀錄 + PD 模擬）</div>", unsafe_allow_html=True)

    if st.session_state["user_id"]:
        st.subheader("📜 目前用戶交易紀錄")
        df_rows = list_transactions(st.session_state["user_id"])
        if df_rows:
            df = pd.DataFrame(df_rows, columns=["type", "amount", "timestamp"])
            st.dataframe(df, use_container_width=True)
        else:
            st.info("目前用戶無交易紀錄")

    st.divider()

    st.subheader("📊 模擬 PD 分布 (20 個虛擬用戶)")
    df_pd = pd.DataFrame({
        "User ID": [f"MOCK-{i+1}" for i in range(20)], # 區分實際用戶
        "PD": np.random.uniform(0, 0.5, 20)
    })
    st.bar_chart(df_pd, x="User ID", y="PD")