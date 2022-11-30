import ProcessModelListTiles from '../components/ProcessModelListTiles';

export default function CreateNewInstance() {
  return (
    <ProcessModelListTiles
      headerElement={<h2>Processes I can start</h2>}
      checkPermissions={false}
    />
  );
}
