import json
import os
from dataclasses import dataclass, field, is_dataclass


@dataclass
class CommonApiConfig:
    test_mode: bool = False
    test_mode_port: int = 8080  # Default port, can be overridden
    api_key: str = ""
    secrets_dir:str=""
    backend_base_uri: str = "/fastapi/"
    firebase_api_key: str = ""
    firebase_sp_path: str = ""
    firestore_collections: list[str] = field(default_factory=lambda: [
        "all_user_profiles",
        "firebase_stripe_mappings",
        'plan_files',
        "layer_matchings",
        "ccc"
    ])
    stripe_api_key: str = ""
    firebase_base_url: str = "https://identitytoolkit.googleapis.com/v1/accounts:"
    firebase_refresh_token = f"{firebase_base_url[:-9]}token?key="  ## Change
    firebase_signInWithPassword = f"{firebase_base_url}signInWithPassword?key="
    firebase_sendOobCode = f"{firebase_base_url}sendOobCode?key="
    firebase_resetPassword = f"{firebase_base_url}resetPassword?key="
    firebase_signInWithCustomToken = f"{firebase_base_url}signInWithCustomToken?key="
    firebase_update = f"{firebase_base_url}update?key="
    enable_CORS_url: str = "http://localhost:3000"
    reset_password: str = backend_base_uri + "reset-password"
    confirm_reset: str = backend_base_uri + "confirm-reset"
    change_password: str = backend_base_uri + "change-password"
    change_email: str = backend_base_uri + "change_email"
    login: str = backend_base_uri + "login"
    refresh_token: str = backend_base_uri + "refresh-token"
    user_profile: str = backend_base_uri + "user_profile"

    # Stripe Product URLs
    create_stripe_product: str = backend_base_uri + "create_stripe_product"
    update_stripe_product: str = backend_base_uri + "update_stripe_product"
    delete_stripe_product: str = backend_base_uri + "delete_stripe_product"
    list_stripe_products: str = backend_base_uri + "list_stripe_products"

    # Stripe wallet URLs
    top_up_wallet: str = backend_base_uri + "top_up_wallet"
    fetch_wallet: str = backend_base_uri + "fetch_wallet"
    deduct_wallet: str = backend_base_uri + "deduct_wallet"

    # Stripe customers
    create_stripe_customer: str = backend_base_uri + "create_stripe_customer"
    update_stripe_customer: str = backend_base_uri + "update_stripe_customer"
    fetch_stripe_customer: str = backend_base_uri + "fetch_stripe_customer"
    delete_stripe_customer: str = backend_base_uri + "delete_stripe_customer"
    list_stripe_customers: str = backend_base_uri + "list_stripe_customers"
    get_customer_spending: str = backend_base_uri + "get_customer_spending"

    # Stripe Subscription
    create_stripe_subscription: str = backend_base_uri + "create_stripe_subscription"
    update_stripe_subscription: str = backend_base_uri + "update_stripe_subscription"
    deactivate_stripe_subscription: str = (
        backend_base_uri + "deactivate_stripe_subscription"
    )
    fetch_stripe_subscription: str = backend_base_uri + "fetch_stripe_subscription"

    # Stripe Payment Methods
    create_stripe_payment_method: str = (
        backend_base_uri + "create_stripe_payment_method"
    )
    update_stripe_payment_method: str = (
        backend_base_uri + "update_stripe_payment_method"
    )
    detach_stripe_payment_method: str = (
        backend_base_uri + "detach_stripe_payment_method"
    )
    attach_stripe_payment_method: str = (
        backend_base_uri + "attach_stripe_payment_method"
    )
    set_default_stripe_payment_method: str = (
        backend_base_uri + "set_default_stripe_payment_method"
    )
    list_stripe_payment_methods: str = backend_base_uri + "list_stripe_payment_methods"
    testing_create_card_payment_source: str = (
        backend_base_uri + "testing_create_card_payment_source"
    )

    @classmethod
    def get_common_conf(cls):
        conf = cls()

        # Check if we're in test mode
        if os.getenv("TEST_MODE", "false").lower() == "true":
            conf.test_mode = True
            # Use dynamic port from environment if available
            # TEST_SERVER_PORT is set by the test runner after port selection
            # PORT is a fallback for uvicorn and other servers
            # If neither is set, use the default 8080
            test_port = os.getenv("TEST_SERVER_PORT") or os.getenv("PORT")
            if test_port:
                try:
                    conf.test_mode_port = int(test_port)
                except (ValueError, TypeError):
                    # If port is not a valid integer, keep default
                    conf.test_mode_port = 8080
            else:
                conf.test_mode_port = 8080

        if conf.test_mode:
            conf.secrets_dir = "secrets_test"
        else:
            conf.secrets_dir = "secrets"

        try:
            if os.path.exists(f"{conf.secrets_dir}/secrets_firebase.json"):
                with open(
                    f"{conf.secrets_dir}/secrets_firebase.json", "r", encoding="utf-8"
                ) as config_file:
                    data = json.load(config_file)
                    conf.firebase_api_key = data.get("firebase_api_key", "")
                    conf.firebase_sp_path = data.get("firebase_sp_path", "")

            if os.path.exists(f"{conf.secrets_dir}/secret_stripe.json"):
                with open(f"{conf.secrets_dir}/secret_stripe.json", "r", encoding="utf-8") as config_file:
                    data = json.load(config_file)
                    conf.stripe_api_key = data.get("stripe_api_key", "")

            return conf
        except Exception as _:
            return conf


CONF = CommonApiConfig.get_common_conf()
