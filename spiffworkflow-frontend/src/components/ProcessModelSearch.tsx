import {
  ComboBox,
  // @ts-ignore
} from '@carbon/react';
import { truncateString } from '../helpers';
import { ProcessModel } from '../interfaces';

type OwnProps = {
  onChange: (..._args: any[]) => any;
  processModels: ProcessModel[];
  selectedItem?: ProcessModel | null;
};

export default function ProcessModelSearch({
  processModels,
  selectedItem,
  onChange,
}: OwnProps) {
  const shouldFilterProcessModel = (options: any) => {
    const processModel: ProcessModel = options.item;
    const { inputValue } = options;
    return `${processModel.process_group_id}/${processModel.id} (${processModel.display_name})`.includes(
      inputValue
    );
  };
  return (
    <ComboBox
      onChange={onChange}
      id="process-model-select"
      items={processModels}
      itemToString={(processModel: ProcessModel) => {
        if (processModel) {
          return `${processModel.process_group_id}/${
            processModel.id
          } (${truncateString(processModel.display_name, 20)})`;
        }
        return null;
      }}
      shouldFilterItem={shouldFilterProcessModel}
      placeholder="Choose a process model"
      titleText="Process model"
      selectedItem={selectedItem}
    />
  );
}
