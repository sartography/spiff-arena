import ProcessModelListTiles from '../components/ProcessModelListTiles';

export default function CreateNewInstance() {
  return (
    <ProcessModelListTiles
      headerElement={<h2>Process Models I can start</h2>}
      checkPermissions={false}
    />
  );
}
