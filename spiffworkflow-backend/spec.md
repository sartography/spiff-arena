Messages are saved on the process group - but you can't dictate on which process group.
So when you are in the message modal, it shows the current location based on the process group where the message is saved.
But as you can see, the location is also stored in the db.
We should be able to update the location for an existing message.
And if a message already exists at a certain parent location, and you are editing a process model that is in a child directory, it should assume you want to use the message in the parent directory (but you should be able to override this assumption).
This involves frontend, and will require testing in a browser.
The API may not know that things are being updated on a particular message (and therefore might naively just create a new message at a new location, instead of updating as intended).
Perhaps there is a new interface for editing messages, since it is kind of confusing to edit them from the context of a particular process model when in fact messages are specific to a process group and potentially shared across multiple process models.

> mysql -uroot spiffworkflow_backend_local_development -e 'select \* from message'
> +------+--------------------------------------------+-------------------------------------+--------+-----------------------+-----------------------+
> | id | identifier | location | schema | updated_at_in_seconds | created_at_in_seconds |
> +------+--------------------------------------------+-------------------------------------+--------+-----------------------+-----------------------+
> | 1439 | awesome-order-start | order | {} | 1771903745 | 1771903745 |
> | 1440 | document-uploaded | order | {} | 1771903745 | 1771903745 |
> | 1441 | request-for-information-received | order | {} | 1771903745 | 1771903745 |
> | 1442 | survey-request-fulfilled | order | {} | 1771903745 | 1771903745 |
> | 1443 | title-search-completed | order | {} | 1771903745 | 1771903745 |
> | 1444 | request-for-information-received | order/request-for-information | {} | 1771903745 | 1771903745 |
> | 1445 | reuest-for-information-received | order/request-for-information | {} | 1771903745 | 1771903745 |
> | 1446 | document-uploaded | order/order-survey | {} | 1771903745 | 1771903745 |
> | 1447 | order-survey-endpoint | order/order-survey | {} | 1771903745 | 1771903745 |
> | 1448 | survey-request-fulfilled | order/order-survey | {} | 1771903745 | 1771903745 |
> | 1449 | request-for-information-received | order/residential | {} | 1771903745 | 1771903745 |
> | 1450 | reuest-for-information-received | order/residential | {} | 1771903745 | 1771903745 |
> | 1451 | title-search-completed | order/order-title-search | {} | 1771903745 | 1771903745 |
> | 1452 | awesome-hello-world | training-and-prototypes | {} | 1771903745 | 1771903745 |
> | 1453 | decision | training-and-prototypes | {} | 1771903745 | 1771903745 |
> | 1454 | documents | training-and-prototypes | {} | 1771903745 | 1771903745 |
> | 1455 | lilimessages | training-and-prototypes | {} | 1771903745 | 1771903745 |
> | 1456 | process-documents | training-and-prototypes | {} | 1771903745 | 1771903745 |
> | 1457 | awesome-order-survey-start | shared/order-survey | {} | 1771903745 | 1771903745 |
> | 1458 | awesome-order-title-search-start | shared/order-title-search | {} | 1771903745 | 1771903745 |
> | 1459 | start-message-diagram-edit-acceptance-test | system/diagram-edit-acceptance-test | {} | 1771903745 | 1771903745 |
> +------+--------------------------------------------+-------------------------------------+--------+-----------------------+-----------------------+
