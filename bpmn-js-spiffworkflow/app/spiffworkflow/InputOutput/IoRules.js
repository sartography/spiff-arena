import inherits from 'inherits';
import RuleProvider from 'diagram-js/lib/features/rules/RuleProvider';

const HIGH_PRIORITY = 1500;

/**
 * A custom rule provider that will permit Data Inputs and Data
 * Outputs to be placed within a process element (something BPMN.io currently denies)
 *
 * See {@link BpmnRules} for the default implementation
 * of BPMN 2.0 modeling rules provided by bpmn-js.
 *
 * @param {EventBus} eventBus
 */
export default function IoRules(eventBus) {
  RuleProvider.call(this, eventBus);
}

inherits(IoRules, RuleProvider);

IoRules.$inject = [ 'eventBus' ];

IoRules.prototype.init = function() {
  this.addRule('shape.create', HIGH_PRIORITY, function(context) {

    let element = context.shape;
    let target = context.target;
    let position = context.position;

    return canCreate(element, target, position);
  });
};

/**
 * Allow folks to drop a dataInput or DataOutput only on the top level process.
 */
function canCreate(element, target, position) {
  if ([ 'bpmn:DataInput', 'bpmn:DataOutput' ].includes(element.type)) {
    if (target.type == 'bpmn:Process') {
      return true;
    }
  }
}

IoRules.prototype.canCreate = canCreate;
