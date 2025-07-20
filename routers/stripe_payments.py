"""
Stripe router module
Handles all Stripe payment related endpoints including customers, products, subscriptions, 
payment methods, and wallet operations
"""

import uuid
from fastapi import APIRouter
from all_types.request_dtypes import ReqModel
from all_types.response_dtypes import ResModel
from all_types.internal_types import UserId
from backend_common.request_processor import request_handling
from backend_common.dtypes.stripe_dtypes import (
    ProductReq,
    CustomerReq,
    SubscriptionCreateReq,
    SubscriptionUpdateReq,
    PaymentMethodUpdateReq,
    PaymentMethodAttachReq,
    TopUpWalletReq,
    DeductWalletReq,
)
from backend_common.stripe_backend import (
    create_stripe_product,
    update_stripe_product,
    delete_stripe_product,
    list_stripe_products,
    update_customer,
    list_customers,
    get_customer_spending,
    fetch_customer,
    create_subscription,
    update_subscription,
    deactivate_subscription,
    update_payment_method,
    attach_payment_method,
    delete_payment_method,
    list_payment_methods,
    set_default_payment_method,
    top_up_wallet,
    fetch_wallet,
    deduct_from_wallet,
)
from config_factory import CONF


stripe_router = APIRouter()


# Stripe Customers
@stripe_router.post(
    CONF.get_customer_spending,
    response_model=ResModel[dict],
    description="Get all spending history for a specific customer",
    tags=["stripe customers"],
)
async def get_customer_spending_endpoint(req: UserId):
    response = await request_handling(
        req, UserId, ResModel[dict], get_customer_spending, wrap_output=True
    )
    return response


@stripe_router.put(
    CONF.update_stripe_customer,
    response_model=ResModel[dict],
    description="Update an existing customer in stripe",
    tags=["stripe customers"],
)
async def update_stripe_customer_endpoint(req: ReqModel[CustomerReq]):
    response = await request_handling(
        req.request_body,
        CustomerReq,
        ResModel[dict],
        update_customer,
        wrap_output=True,
    )
    return response


@stripe_router.get(
    CONF.list_stripe_customers,
    response_model=ResModel[list[dict]],
    description="list all customers in stripe",
    tags=["stripe customers"],
)
async def list_stripe_customers_endpoint():
    response = await request_handling(
        None, None, ResModel[list[dict]], list_customers, wrap_output=True
    )
    return response


@stripe_router.post(
    CONF.fetch_stripe_customer,
    response_model=ResModel[dict],
    description="Fetch a customer in stripe",
    tags=["stripe customers"],
)
async def fetch_stripe_customer_endpoint(req: ReqModel[UserId]):
    response = await request_handling(
        req.request_body,
        UserId,
        ResModel[dict],
        fetch_customer,
        wrap_output=True,
    )
    return response


# Stripe Wallet
@stripe_router.post(
    CONF.top_up_wallet,
    description="top_up a customer's wallet in stripe",
    tags=["stripe wallet"],
    response_model=ResModel[dict],
)
async def top_up_wallet_endpoint(req: ReqModel[TopUpWalletReq]):
    response = await request_handling(
        req.request_body,
        TopUpWalletReq,
        ResModel[dict],
        top_up_wallet,
        wrap_output=True,
    )
    return response


@stripe_router.get(
    CONF.fetch_wallet,
    description="Fetch a customer's wallet in stripe",
    tags=["stripe wallet"],
    response_model=ResModel[dict],
)
async def fetch_wallet_endpoint(user_id: str):
    resp = await fetch_wallet(user_id)
    response = ResModel(
        data=resp,
        message="Wallet fetched successfully",
        request_id=str(uuid.uuid4()),
    )
    return response


@stripe_router.post(
    CONF.deduct_wallet,
    description="Deduct amount from customer's wallet in stripe",
    tags=["stripe wallet"],
    response_model=ResModel[dict],
)
async def deduct_from_wallet_endpoint(req: ReqModel[DeductWalletReq]):
    response = await request_handling(
        req.request_body,
        DeductWalletReq,
        ResModel[dict],
        deduct_from_wallet,
        wrap_output=True,
    )
    return response


# Stripe Subscriptions
@stripe_router.post(
    CONF.create_stripe_subscription,
    description="Create a new subscription in stripe",
    tags=["stripe subscriptions"],
    response_model=ResModel[dict],
)
async def create_stripe_subscription_endpoint(
    req: ReqModel[SubscriptionCreateReq],
):
    subscription = await create_subscription(req.request_body)
    response = ResModel(
        data=subscription,
        message="Subscription created successfully",
        request_id=str(uuid.uuid4()),
    )
    return response


@stripe_router.put(
    CONF.update_stripe_subscription,
    response_model=ResModel[dict],
    description="Update an existing subscription in stripe",
    tags=["stripe subscriptions"],
)
async def update_stripe_subscription_endpoint(
    subscription_id: str, req: ReqModel[SubscriptionUpdateReq]
):
    subscription = await update_subscription(
        subscription_id, req.request_body.seats
    )
    response = ResModel(
        data=subscription,
        message="Subscription updated successfully",
        request_id=str(uuid.uuid4()),
    )
    return response


@stripe_router.delete(
    CONF.deactivate_stripe_subscription,
    response_model=ResModel[dict],
    description="Deactivate an existing subscription in stripe",
    tags=["stripe subscriptions"],
)
async def deactivate_stripe_subscription_endpoint(subscription_id: str):
    deactivated = await deactivate_subscription(subscription_id)
    response = ResModel(
        data=deactivated,
        message="Subscription deactivated successfully",
        request_id=str(uuid.uuid4()),
    )
    return response


# Stripe Payment Methods
@stripe_router.put(
    CONF.update_stripe_payment_method,
    response_model=ResModel[dict],
    description="Update an existing payment method in stripe",
    tags=["stripe payment methods"],
)
async def update_stripe_payment_method_endpoint(
    payment_method_id: str, req: ReqModel[PaymentMethodUpdateReq]
):
    payment_method = await update_payment_method(
        payment_method_id, req.request_body
    )
    response = ResModel(
        data=payment_method,
        message="Payment method updated successfully",
        request_id=str(uuid.uuid4()),
    )
    return response


@stripe_router.post(
    CONF.attach_stripe_payment_method,
    response_model=ResModel[dict],
    description="Add an existing stripe payment method to a customer",
    tags=["stripe payment methods"],
)
async def attach_stripe_payment_method_endpoint(
    req: ReqModel[PaymentMethodAttachReq],
):
    data = await attach_payment_method(
        req.request_body.user_id, req.request_body.payment_method_id
    )
    response = ResModel(
        data=data,
        message="Payment method attached successfully",
        request_id=str(uuid.uuid4()),
    )
    return response


@stripe_router.delete(
    CONF.detach_stripe_payment_method,
    response_model=ResModel[dict],
    description="Delete an existing payment method in stripe",
    tags=["stripe payment methods"],
)
async def delete_stripe_payment_method_endpoint(payment_method_id: str):
    data = await delete_payment_method(payment_method_id)
    response = ResModel(
        data=data,
        message="Payment method deleted successfully",
        request_id=str(uuid.uuid4()),
    )
    return response


@stripe_router.get(
    CONF.list_stripe_payment_methods,
    response_model=ResModel[list[dict]],
    description="list all payment methods in stripe",
    tags=["stripe payment methods"],
)
async def list_stripe_payment_methods_endpoint(user_id: str):
    payment_methods = await list_payment_methods(user_id)
    response = ResModel(
        data=payment_methods,
        message="Payment methods retrieved successfully",
        request_id=str(uuid.uuid4()),
    )
    return response


@stripe_router.put(
    CONF.set_default_stripe_payment_method,
    response_model=ResModel[dict],
    description="Set a default payment method in stripe",
    tags=["stripe payment methods"],
)
async def set_default_payment_method_endpoint(
    user_id: str, payment_method_id: str
):
    default_payment_method = await set_default_payment_method(
        user_id, payment_method_id
    )
    response = ResModel(
        data=default_payment_method,
        message="Default payment method set successfully",
        request_id=str(uuid.uuid4()),
    )
    return response


# Stripe Products
@stripe_router.post(
    CONF.create_stripe_product,
    response_model=ResModel[dict],
    description="Create a new subscription product in stripe",
    tags=["stripe products"],
)
async def create_stripe_product_endpoint(req: ReqModel[ProductReq]):
    product = await create_stripe_product(req.request_body)

    response = ResModel(
        data=product,
        message="Product created successfully",
        request_id=str(uuid.uuid4()),
    )
    return response


@stripe_router.put(
    CONF.update_stripe_product,
    response_model=ResModel[dict],
    description="Update an existing subscription product in stripe",
    tags=["stripe products"],
)
async def update_stripe_product_endpoint(
    product_id: str, req: ReqModel[ProductReq]
):
    product = await update_stripe_product(product_id, req.request_body)
    response = ResModel(
        data=product,
        message="Product updated successfully",
        request_id=str(uuid.uuid4()),
    )

    return response.model_dump()


@stripe_router.delete(
    CONF.delete_stripe_product,
    response_model=ResModel[dict],
    description="Delete an existing subscription product in stripe",
    tags=["stripe products"],
)
async def delete_stripe_product_endpoint(product_id: str):
    deleted = await delete_stripe_product(product_id)
    response = ResModel(
        data=deleted,
        message="Product deleted successfully",
        request_id=str(uuid.uuid4()),
    )
    return response


@stripe_router.get(
    CONF.list_stripe_products,
    description="list all subscription products in stripe",
    tags=["stripe products"],
    response_model=ResModel[list[dict]],
)
async def list_stripe_products_endpoint():
    products = await list_stripe_products()
    response = ResModel(
        data=products,
        message="Products retrieved successfully",
        request_id=str(uuid.uuid4()),
    )
    return response
