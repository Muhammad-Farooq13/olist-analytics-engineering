{% macro generate_schema_name(custom_schema_name, node) -%}
    {#-
        By default dbt prefixes custom schemas with the target schema
        (e.g. "main_staging"). For a small local DuckDB warehouse that's
        just noise — this macro uses the custom schema name as-is, so
        models land cleanly in `staging` and `marts`.
    -#}
    {%- if custom_schema_name is none -%}
        {{ target.schema }}
    {%- else -%}
        {{ custom_schema_name | trim }}
    {%- endif -%}
{%- endmacro %}
