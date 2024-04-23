import ProcessModelListTiles from '../components/ProcessModelListTiles';

export default function CreateNewInstance() {
  return (
    <ProcessModelListTiles
      headerElement={<h2>Processos que posso iniciar</h2>}
      checkPermissions={false}
    />
  );
}
