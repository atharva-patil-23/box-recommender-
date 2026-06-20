# Test & Quality-Gate Output

Captured: 2026-06-20 09:46:50 UTC
Environment: Python 3.13.3, Django 5.1.4, PostgreSQL 16 (Docker), `DATABASE_URL`-driven.

These are the four gates the GitHub Actions workflow runs, in order.

## 1. ruff (lint + format)
```
All checks passed!
28 files already formatted
```

## 2. mypy (strict, django-stubs + drf-stubs)
```
Success: no issues found in 25 source files
```

## 3. Migration drift check
```
$ python manage.py makemigrations --check --dry-run
No changes detected
```

## 4. pytest (with >=90% coverage gate)
```
============================= test session starts ==============================
platform darwin -- Python 3.13.3, pytest-8.3.4, pluggy-1.6.0 -- /Users/atharva/Developer/tradexa_tech_assignment/.venv/bin/python
cachedir: .pytest_cache
django: version: 5.1.4, settings: config.settings (from ini)
rootdir: /Users/atharva/Developer/tradexa_tech_assignment
configfile: pyproject.toml
plugins: cov-6.0.0, django-4.9.0
collecting ... collected 26 items

inventory/tests.py::test_product_volume_and_str PASSED                   [  3%]
inventory/tests.py::test_box_volume_and_str PASSED                       [  7%]
inventory/tests.py::test_seed_demo_is_idempotent PASSED                  [ 11%]
orders/test_api.py::test_recommends_cheapest_fitting_box_and_persists_order PASSED [ 15%]
orders/test_api.py::test_returns_no_fit_when_order_too_large PASSED      [ 19%]
orders/test_api.py::test_rejects_empty_items PASSED                      [ 23%]
orders/test_api.py::test_rejects_unknown_product PASSED                  [ 26%]
orders/test_api.py::test_rejects_zero_quantity PASSED                    [ 30%]
orders/test_api.py::test_rejects_quantity_above_max PASSED               [ 34%]
orders/test_api.py::test_rejects_duplicate_products PASSED               [ 38%]
orders/tests.py::test_order_and_item_str PASSED                          [ 42%]
selection/tests.py::test_dimensions_fit_exact PASSED                     [ 46%]
selection/tests.py::test_dimensions_fit_rejects_when_one_side_too_big PASSED [ 50%]
selection/tests.py::test_item_fits_box_allows_rotation PASSED            [ 53%]
selection/tests.py::test_order_fits_box_happy_path PASSED                [ 57%]
selection/tests.py::test_order_rejected_when_total_volume_exceeds_box PASSED [ 61%]
selection/tests.py::test_order_rejected_when_total_weight_exceeds_capacity PASSED [ 65%]
selection/tests.py::test_order_rejected_when_single_item_too_large_by_dimension PASSED [ 69%]
selection/tests.py::test_recommend_picks_cheapest_fitting_box PASSED     [ 73%]
selection/tests.py::test_recommend_tie_breaks_cheapest_by_smallest_volume PASSED [ 76%]
selection/tests.py::test_recommend_tie_breaks_by_name_when_cost_and_volume_equal PASSED [ 80%]
selection/tests.py::test_recommendation_reports_utilisation PASSED       [ 84%]
selection/tests.py::test_recommend_returns_no_fit_when_nothing_holds_the_order PASSED [ 88%]
selection/tests.py::test_recommend_no_fit_when_box_list_is_empty PASSED  [ 92%]
selection/tests.py::test_recommend_raises_on_empty_order PASSED          [ 96%]
selection/tests.py::test_recommend_considers_multiple_items_together PASSED [100%]

---------- coverage: platform darwin, python 3.13.3-final-0 ----------
Name                                         Stmts   Miss  Cover   Missing
--------------------------------------------------------------------------
inventory/management/commands/seed_demo.py      15      0   100%
inventory/models.py                             32      0   100%
orders/api.py                                   24      0   100%
orders/models.py                                19      0   100%
orders/serializers.py                           15      0   100%
orders/services.py                              27      0   100%
orders/test_api.py                              70      0   100%
orders/urls.py                                   4      0   100%
selection/engine.py                             29      0   100%
selection/types.py                              45      0   100%
--------------------------------------------------------------------------
TOTAL                                          280      0   100%

Required test coverage of 90% reached. Total coverage: 100.00%

============================== 26 passed in 0.52s ==============================
```
