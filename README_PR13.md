
# PR13 – Validator Tool

* `app/validators.py` basic regex money/email.
* `app/validator_tool.py` callable by Assistants.
* Add `validator` block in slot YAML: 
  ```yaml
  validator: {type: money, max_retries: 1}
  ```
