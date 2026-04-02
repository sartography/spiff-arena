need new page for message models that shows a list of them, including their identifiers, locations
do we already cache which process models use which messages? if so, including this information would be nice.
you can edit one message from the message model list.
this should present a UX similar to the current message editor modal that is now only accessible when editing a particular process model bpmn.
If you add a message, it needs to be added to the correct process_group.json
Same with editing, and deleting, it needs to update the db cache of messages, and also update the filesystem process_group.json
When editing a process model bpmn, you should just get a list of messages.
You should be allowed to get to the place where you can edit message models, but we'd like to make it more clear that you're just selecting a message model for your process model, not editing from the process model (because that message model may be used elsewhere, and ideally that other UX message editing UX should tell you as much).
There is an existing bug where if you open the message modal from a process model, save from within that dialog, and then save the process model bpmn, it will change the correlationKey, like this:

```
-  <bpmn:correlationKey id="CorrelationKey_02wv8uq" name="MainCorrelationKey">
+  <bpmn:correlationKey id="CorrelationKey_142qnol" name="MainCorrelationKey">
```

it always gets a new id.
this seems not great.
then, also, if you go and open the message dialog AGAIN, and save twice as before, it will delete the entire correlationKey node.
if you hard refresh after saving the process model bpmn the first time, it will not delete the entire node.
so if we change the way the modal works, these bad symptoms may or may not be affected.
