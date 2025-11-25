import yaml
import numpy as np
import pickle
import os

from utils.db import (
    generate_user_id,
    add_account,
    get_account,
    borrow as db_borrow,
    repay as db_repay
)

class LoanAIPipeline:
    def __init__(self, config_path="config/config.yaml"):
        with open(config_path, "r", encoding="utf-8") as f:
            self.cfg = yaml.safe_load(f)

        self.model = self._load_model()

    # ============================================================
    # Load Model
    # ============================================================
    def _load_model(self):
        model_path = self.cfg["model"]["path"]

        if os.path.exists(model_path):
            try:
                return pickle.load(open(model_path, "rb"))
            except:
                pass

        if self.cfg["model"]["use_mock_model_if_missing"]:
            return None

        raise FileNotFoundError("Model not found and mock model disabled.")

    # ============================================================
    # Step 1: KYC → Feature Engineering
    # ============================================================
    def process_kyc(self, kyc_data: dict):
        features = {
            "age": kyc_data.get("age"),
            "income": kyc_data.get("income")
        }

        # 模擬信用資料
        if self.cfg["feature_engineering"]["simulate_credit_score"]:
            features["credit_score"] = np.random.randint(300, 850)

        if self.cfg["feature_engineering"]["simulate_delay"]:
            features["past_delay"] = np.random.randint(0, 5)

        if self.cfg["feature_engineering"]["simulate_usage"]:
            features["loan_usage"] = float(np.random.uniform(0, 1))

        return features

    # ============================================================
    # Step 2: AI PD 計算
    # ============================================================
    def calculate_pd(self, features: dict):
        if self.model is None:
            return float(np.random.uniform(0, 0.5))

        X = [[
            features["age"],
            features["income"],
            features["credit_score"],
            features["past_delay"],
            features["loan_usage"],
        ]]

        return float(self.model.predict_proba(X)[0][1])

    # ============================================================
    # Step 3: Decision Engine
    # ============================================================
    def decision(self, pd_value):
        reject_th = self.cfg["decision_thresholds"]["reject"]
        review_th = self.cfg["decision_thresholds"]["review"]

        if pd_value > reject_th:
            return "reject"
        elif pd_value > review_th:
            return "review"
        else:
            return "approve"

    # ============================================================
    # Step 4: Credit Limit Calculation
    # ============================================================
    def calculate_limit(self, pd_value):
        if pd_value > self.cfg["decision_thresholds"]["review"]:
            return 0

        base = self.cfg["limit_rule"]["base_amount"]
        var = self.cfg["limit_rule"]["variable_amount"]

        return int(base + (1 - pd_value) * var)

    # ============================================================
    # Step 5: 建立帳戶
    # ============================================================
    def create_user(self, kyc_data, pd_value, limit):
        """
        產生 user_id → 寫入 DB → 回傳 user_id
        """
        user_id = generate_user_id(kyc_data["name"], kyc_data["national_id_last4"])
        add_account(user_id, kyc_data["name"], pd_value, limit)
        return user_id

    # ============================================================
    # Step 6: 借款
    # ============================================================
    def borrow(self, user_id, amount):
        acct = get_account(user_id)
        if acct is None:
            return {"success": False, "msg": "找不到帳戶"}

        available = acct["available_credit"]

        if amount > available:
            return {"success": False, "msg": "超過可用額度"}

        db_borrow(user_id, amount)

        new_acct = get_account(user_id)
        return {
            "success": True,
            "after_balance": new_acct["outstanding_balance"]
        }

    # ============================================================
    # Step 7: 還款
    # ============================================================
    def repay(self, user_id, amount):
        acct = get_account(user_id)
        if acct is None:
            return {"success": False, "msg": "找不到帳戶"}

        outstanding = acct["outstanding_balance"]

        if amount > outstanding:
            return {"success": False, "msg": "還款金額 > 尚未償還金額"}

        db_repay(user_id, amount)

        new_acct = get_account(user_id)
        return {
            "success": True,
            "after_balance": new_acct["outstanding_balance"]
        }
