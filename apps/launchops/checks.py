from django.core.checks import Error, Warning, register

from .status import collect_launch_checks


@register(deploy=True)
def avan_deployment_checks(app_configs, **kwargs):
    messages = []
    for item in collect_launch_checks(include_dependencies=False):
        if item.ok:
            continue
        cls = Error if item.critical else Warning
        messages.append(
            cls(
                item.label,
                hint=item.detail,
                id=f"avan.E13{len(messages) + 1:02d}" if item.critical else f"avan.W13{len(messages) + 1:02d}",
            )
        )
    return messages
