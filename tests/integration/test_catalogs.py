"""
Test cases for catalog management endpoints using the ConfigDrivenTest framework.

This module provides compreh                }
            ).model_dump()
        }
        },
        expected_output={
            "status_code": 200,
            "response_body": {
                "message": "Request received.",
                "request_id": "min_length:1",
                "data": "regex:^[0-9a-f-]{36}$"
            },
        },ation tests for the save catalog endpoint,
testing various scenarios including simple catalog creation and complex catalogs with display elements.
"""

from .fixtures.test_utils import create_parametrized_test
from .fixtures.test_generator import ConfigDrivenTest, Prerequisites, Endpoint
from all_types.request_dtypes import ReqSavePrdcerCtlg


# Catalog tests for comprehensive save catalog endpoint testing
CATALOG_MANAGEMENT_TESTS = [
    ConfigDrivenTest(
        name="test_save_catalog_simple",
        description="Test saving a simple catalog with basic layer information",
        prerequisites=Prerequisites(
            requires_user=True,
            requires_auth=True,
            requires_database_seed=True,
            user_type="admin",
            firebase_profile_seeds=["admin_profile_with_datasets"]
        ),
        endpoint=Endpoint(method="POST", path="/save_producer_catalog"),
        input_data={
            "_form_data": True,  # Special flag to indicate form data
            "req": {  # This will be serialized as JSON string in the "req" field
                "message": "Save simple catalog request",
                "request_info": {"request_id": "test-catalog-simple-001"},
                "request_body": ReqSavePrdcerCtlg(
                    prdcer_ctlg_name="Simple Retail Catalog",
                    subscription_price="99",
                    ctlg_description="A simple catalog containing retail locations",
                    total_records=100,
                    lyrs=[
                        {
                            "layer_id": "l09a5e6ed-d22e-4db0-a0bd-cf0a0bd93548",
                            "points_color": "#FF5733"
                        }
                    ],
                    user_id="${user.user_id}",
                    display_elements={}
                ).model_dump()
            }
            # "image": None  # Optional image field - not included for this test
        },
        expected_output={
            "status_code": 200,
            "response_body": {
                "message": "Request received.",
                "request_id": "min_length:1",
                "data": "regex:^[0-9a-f-]{36}$"
            },
        },
    ),

    ConfigDrivenTest(
        name="test_save_catalog_complex",
        description="Test saving a complex catalog with detailed display elements and markers",
        prerequisites=Prerequisites(
            requires_user=True,
            requires_auth=True,
            requires_database_seed=True,
            user_type="admin",
            firebase_profile_seeds=["admin_profile_with_datasets"]
        ),
        endpoint=Endpoint(method="POST", path="/save_producer_catalog"),
        input_data={
            "_form_data": True,
            "req": {
                "message": "Save complex catalog request",
                "request_info": {"request_id": "test-catalog-complex-001"},
                "request_body": ReqSavePrdcerCtlg(
                    prdcer_ctlg_name="Complex Riyadh Catalog",
                    subscription_price="199",
                    ctlg_description="A comprehensive catalog with detailed analysis",
                    total_records=500,
                    lyrs=[
                        {
                            "layer_id": "l46d94c68-736e-40ba-bb6a-864bb5a2da49",
                            "points_color": "#28A745"
                        }
                    ],
                    user_id="${user.user_id}",
                    display_elements={
                        "details": [
                            {
                                "display": True,
                                "points_color": "#28A745",
                                "is_enabled": True,
                                "opacity": 1
                            }
                        ],
                        "markers": [
                            {
                                "id": "504569ed-9b46-436e-86fd-b28543a5e2dc",
                                "name": "Highest Population Center",
                                "lat": 24.7136,
                                "lng": 46.6753,
                                "color": "#FF6B35",
                                "icon": "population"
                            }
                        ],
                        "case_study": [
                            {
                                "type": "heading-one",
                                "direction": "rtl",
                                "align": "right",
                                "children": [
                                    {
                                        "text": "تحليل شامل للموقع",
                                        "bold": True
                                    }
                                ]
                            }
                        ],
                        "polygons": []
                    }
                ).model_dump()
            }
        },
        expected_output={
            "status_code": 200,
            "response_body": {
                "message": "Request received.",
                "request_id": "min_length:1",
                "data": "regex:^[0-9a-f-]{36}$"
            },
        },
    ),

    ConfigDrivenTest(
        name="test_save_catalog_arabic_content",
        description="Test saving catalog with Arabic content in name and description",
        prerequisites=Prerequisites(
            requires_user=True,
            requires_auth=True,
            requires_database_seed=True,
            user_type="admin",
            firebase_profile_seeds=["admin_profile_with_datasets"]
        ),
        endpoint=Endpoint(method="POST", path="/save_producer_catalog"),
        input_data={
            "_form_data": True,
            "req": {
                "message": "Save Arabic catalog request",
                "request_info": {"request_id": "test-catalog-arabic-001"},
                "request_body": ReqSavePrdcerCtlg(
                    prdcer_ctlg_name="كتالوج المطاعم في الرياض",
                    subscription_price="149",
                    ctlg_description="كتالوج شامل للمطاعم والمقاهي في مدينة الرياض",
                    total_records=300,
                    lyrs=[
                        {
                            "layer_id": "l09a5e6ed-d22e-4db0-a0bd-cf0a0bd93548",
                            "points_color": "#FF5733"
                        }
                    ],
                    user_id="${user.user_id}",
                    display_elements={
                        "details": [
                            {
                                "display": True,
                                "points_color": "#FF5733",
                                "is_enabled": True,
                                "opacity": 1
                            }
                        ],
                        "case_study": [
                            {
                                "type": "heading-one",
                                "direction": "rtl",
                                "align": "right",
                                "children": [
                                    {
                                        "text": "دراسة تحليلية للمطاعم",
                                        "bold": True
                                    }
                                ]
                            },
                            {
                                "type": "paragraph",
                                "direction": "rtl",
                                "align": "right",
                                "children": [
                                    {
                                        "text": "تحليل شامل لتوزيع المطاعم في أحياء الرياض"
                                    }
                                ]
                            }
                        ]
                    }
                ).model_dump()
            }
        },
        expected_output={
            "status_code": 200,
            "response_body": {
                "message": "Request received.",
                "request_id": "min_length:1",
                "data": "regex:^[0-9a-f-]{36}$"
            },
        },
    ),

    ConfigDrivenTest(
        name="test_save_catalog_with_polygons",
        description="Test saving catalog with complex polygon data, measurements, and markers",
        prerequisites=Prerequisites(
            requires_user=True,
            requires_auth=True,
            requires_database_seed=True,
            user_type="admin",
            firebase_profile_seeds=["admin_profile_with_datasets"]
        ),
        endpoint=Endpoint(method="POST", path="/save_producer_catalog"),
        input_data={
            "_form_data": True,
            "req": {
                "message": "Save catalog with polygon data",
                "request_info": {"request_id": "test-catalog-polygons-001"},
                "request_body": ReqSavePrdcerCtlg(
                    prdcer_ctlg_name="Riyadh Geographic Analysis",
                    subscription_price="299",
                    ctlg_description="Comprehensive geographic analysis with polygon data and measurements",
                    total_records=750,
                    lyrs=[
                        {
                            "layer_id": "l46d94c68-736e-40ba-bb6a-864bb5a2da49",
                            "points_color": "#28A745"
                        }
                    ],
                    user_id="${user.user_id}",
                    display_elements={
                        "details": [
                            {
                                "display": True,
                                "points_color": "#28A745",
                                "is_enabled": True,
                                "opacity": 1
                            }
                        ],
                        "markers": [
                            {
                                "id": "504569ed-9b46-436e-86fd-b28543a5e2dc",
                                "name": "Highest Population Center",
                                "description": "",
                                "coordinates": [46.711970476802776, 24.639665540457955],
                                "timestamp": 1748737881336
                            },
                            {
                                "id": "c656da34-5c12-4b60-af53-4fda2109cf99",
                                "name": "High Population South",
                                "description": "",
                                "coordinates": [46.77422159015896, 24.56590036315339],
                                "timestamp": 1748737893915
                            },
                            {
                                "id": "e72e7750-a2a4-4ba7-959a-01bad0914918",
                                "name": "High Population East",
                                "description": "",
                                "coordinates": [46.83290091832305, 24.715704767489058],
                                "timestamp": 1748737904894
                            }
                        ],
                        "measurements": [
                            {
                                "id": "56e30e84-1e94-4f70-b9a7-214c5a737166",
                                "name": "WH1",
                                "description": "",
                                "sourcePoint": [46.75208141975722, 24.583634094319436],
                                "destinationPoint": [46.71217483445179, 24.63543393050358],
                                "distance": 8.06,
                                "duration": 10.52,
                                "timestamp": 1748738954644
                            },
                            {
                                "id": "a23eddc6-37cf-4900-b1a2-79a97876e767",
                                "name": "WH2",
                                "description": "",
                                "sourcePoint": [46.759533854362815, 24.58975502337728],
                                "destinationPoint": [46.774919525806126, 24.56439494132205],
                                "distance": 4.65,
                                "duration": 8.9,
                                "timestamp": 1748738982900
                            }
                        ],
                        "polygonData": {
                            "sections": [
                                {
                                    "polygon": {
                                        "type": "Feature",
                                        "geometry": {
                                            "type": "MultiPolygon",
                                            "coordinates": [
                                                [
                                                    [
                                                        [46.7519, 24.7489],
                                                        [46.7489, 24.7489],
                                                        [46.7479, 24.7487],
                                                        [46.7485, 24.7485],
                                                        [46.7482, 24.7482],
                                                        [46.7479, 24.7479],
                                                        [46.7474, 24.7474],
                                                        [46.7469, 24.7469],
                                                        [46.7463, 24.7463],
                                                        [46.7456, 24.7456],
                                                        [46.7449, 24.7449],
                                                        [46.7442, 24.7442],
                                                        [46.7434, 24.7434],
                                                        [46.7425, 24.7425],
                                                        [46.7417, 24.7417],
                                                        [46.7408, 24.7408],
                                                        [46.7399, 24.7399],
                                                        [46.7390, 24.7390],
                                                        [46.7382, 24.7382],
                                                        [46.7373, 24.7373],
                                                        [46.7365, 24.7365],
                                                        [46.7357, 24.7357],
                                                        [46.7349, 24.7349],
                                                        [46.7342, 24.7342],
                                                        [46.7336, 24.7336],
                                                        [46.7330, 24.7330],
                                                        [46.7324, 24.7324],
                                                        [46.7320, 24.7320],
                                                        [46.7316, 24.7316],
                                                        [46.7313, 24.7313],
                                                        [46.7311, 24.7311],
                                                        [46.7310, 24.7310],
                                                        [46.7310, 24.7310],
                                                        [46.7311, 24.7311],
                                                        [46.7313, 24.7313],
                                                        [46.7316, 24.7316],
                                                        [46.7320, 24.7320],
                                                        [46.7324, 24.7324],
                                                        [46.7330, 24.7330],
                                                        [46.7336, 24.7336],
                                                        [46.7342, 24.7342],
                                                        [46.7349, 24.7349]
                                                    ]
                                                ]
                                            ]
                                        },
                                        "properties": {
                                            "shape": "circle"
                                        },
                                        "id": "OPr6LkCo3neJsGnLkGvNx2GxREOgFUvt",
                                        "isStatisticsPopupOpen": True,
                                        "pixelPosition": {
                                            "x": 748.0000118746104,
                                            "y": 445.9967320748215
                                        }
                                    },
                                    "sections": [
                                        {
                                            "title": "rating",
                                            "points": [
                                                {
                                                    "layer_name": "SA-RIY-cafe",
                                                    "data": []
                                                }
                                            ]
                                        },
                                        {
                                            "title": "user_ratings_total",
                                            "points": [
                                                {
                                                    "layer_name": "SA-RIY-cafe",
                                                    "data": []
                                                }
                                            ]
                                        }
                                    ],
                                    "areas": ["1KM", "3KM", "5KM"]
                                },
                                {
                                    "polygon": {
                                        "id": "LgNd4HUgRJNZIJDBhlsmLU7naLgd5yNm",
                                        "type": "Feature",
                                        "properties": {
                                            "shape": "polygon"
                                        },
                                        "geometry": {
                                            "coordinates": [
                                                [
                                                    [46.875, 24.875],
                                                    [46.787, 24.787],
                                                    [46.753, 24.753],
                                                    [46.875, 24.875]
                                                ]
                                            ],
                                            "type": "Polygon"
                                        },
                                        "isStatisticsPopupOpen": True,
                                        "pixelPosition": {
                                            "x": 458.69613193890535,
                                            "y": 340.6923703087028
                                        }
                                    },
                                    "sections": [
                                        {
                                            "title": "rating",
                                            "points": [
                                                {
                                                    "layer_name": "SA-RIY-cafe",
                                                    "data": []
                                                }
                                            ]
                                        },
                                        {
                                            "title": "primaryType",
                                            "points": [
                                                {
                                                    "layer_name": "SA-RIY-cafe",
                                                    "data": []
                                                }
                                            ]
                                        }
                                    ],
                                    "areas": ["Unknown"]
                                }
                            ],
                            "benchmarks": [
                                {
                                    "title": "rating",
                                    "value": ""
                                },
                                {
                                    "title": "user_ratings_total",
                                    "value": ""
                                },
                                {
                                    "title": "popularity_score",
                                    "value": ""
                                }
                            ],
                            "isBenchmarkControlOpen": False,
                            "currentStyle": ""
                        },
                        "case_study": [
                            {
                                "direction": "rtl",
                                "children": [
                                    {
                                        "text": "التحليل الديموغرافي"
                                    }
                                ],
                                "align": "right",
                                "type": "heading-one"
                            },
                            {
                                "direction": "rtl",
                                "type": "paragraph",
                                "align": "right",
                                "children": [
                                    {
                                        "text": "تُظهر هذه المنطقة أنماطاً ديموغرافية مثيرة للاهتمام قد تؤثر على قرارات الأعمال والسياسات."
                                    }
                                ]
                            },
                            {
                                "direction": "rtl",
                                "placeholder": "مثال على التحليل الديموغرافي. قم بتعديله لإدراج مخطط معين.",
                                "align": "right",
                                "type": "chart-container",
                                "placeholderType": "demographic",
                                "children": [
                                    {
                                        "text": ""
                                    }
                                ]
                            }
                        ]
                    }
                ).model_dump()
            }
        },
        expected_output={
            "status_code": 200,
            "response_body": {
                "message": "Request received.",
                "request_id": "min_length:1",
                "data": "regex:^[0-9a-f-]{36}$"
            },
        },
    ),
]


# Create the parametrized test using the utility function
test_catalog_management = create_parametrized_test(CATALOG_MANAGEMENT_TESTS)
