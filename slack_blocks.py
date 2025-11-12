def build_kubectl_options_block(user_id, available_commands):
    return {
        "blocks": [
            {
                "type": "section",
                        "text": {
                            "type": "mrkdwn",
                            "text": f"\nHello <@{user_id}>! Select a kubectl command:\n\n"
                        },
                "accessory": {
                            "type": "image",
                            "image_url": "https://raw.githubusercontent.com/kubernetes/kubernetes/master/logo/logo.png",
                            "alt_text": "computer thumbnail"
                        },
            },
            {
                "type": "actions",
                        "elements": [
                            {
                                "type": "static_select",
                                "placeholder": {
                                    "type": "plain_text",
                                    "text": "Select a command"
                                },
                                "options": [
                                    {
                                        "text": {
                                            "type": "plain_text",
                                            "text": command
                                        },
                                        "value": command
                                    }
                                    for command in available_commands
                                ],
                                "action_id": "kubectl_command_select"
                            }
                        ]
            }
        ]
    }


def build_kubectl_sub_command_block(available_sub_commands, selected_command):
    return {
        "blocks": [
           {
               "type": "section",
               "text": {
                   "type": "mrkdwn",
                   "text": "Please select a sub-command:"
               }
           },
            {
               "type": "actions",
               "elements": [
                   {
                       "type": "static_select",
                       "placeholder": {
                           "type": "plain_text",
                           "text": "Select a sub-command"
                       },
                       "options": [
                           {
                               "text": {
                                   "type": "plain_text",
                                   "text": sub_command
                               },
                               "value": sub_command
                           }
                           for sub_command in available_sub_commands.get(selected_command, [])
                       ],
                       "action_id": "kubectl_sub_command_select"
                   }
               ]
           }
        ]
    }


def build_pod_command_block(available_pods):
    return {
        "blocks": [
            {
                "type": "section",
                "text": {
                    "type": "mrkdwn",
                            "text": "Please select a pod:"
                }
            },
            {
                "type": "actions",
                "elements": [
                    {
                        "type": "static_select",
                                "placeholder": {
                                    "type": "plain_text",
                                    "text": "Select a pod"
                                },
                        "options": [
                                    {
                                        "text": {
                                            "type": "plain_text",
                                            "text": pod
                                        },
                                        "value": pod
                                    }
                                    for pod in available_pods
                                ],
                        "action_id": "kubectl_pod_select"
                    }
                ]
            }
        ]
    }


def build_deployments_command_block(available_deployments):
    return {
        "blocks": [
            {
                "type": "section",
                "text": {
                    "type": "mrkdwn",
                            "text": "Please select a deployment:"
                }
            },
            {
                "type": "actions",
                "elements": [
                    {
                        "type": "static_select",
                                "placeholder": {
                                    "type": "plain_text",
                                    "text": "Select a deployment"
                                },
                        "options": [
                                    {
                                        "text": {
                                            "type": "plain_text",
                                            "text": deployment
                                        },
                                        "value": deployment
                                    }
                                    for deployment in available_deployments
                                ],
                        "action_id": "kubectl_deployment_select"
                    }
                ]
            }
        ]
    }


def build_namesapces_block(available_namespaces):
    return {
        "blocks": [
            {
                "type": "section",
                "text": {
                        "type": "mrkdwn",
                        "text": "Please select a namespace:"
                }
            },
            {
                "type": "actions",
                "elements": [
                        {
                            "type": "static_select",
                            "placeholder": {
                                "type": "plain_text",
                                "text": "Select a namespace"
                            },
                            "options": [
                                {
                                    "text": {
                                        "type": "plain_text",
                                        "text": namespace
                                    },
                                    "value": namespace
                                }
                                for namespace in available_namespaces
                            ],
                            "action_id": "kubectl_namespace_select"
                        }
                ]
            }
        ]
    }
