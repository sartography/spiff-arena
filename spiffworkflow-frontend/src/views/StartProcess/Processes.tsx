import ProcessModelTreePage from './ProcessModelTreePage';

export default function Processes({
  setNavElementCallback,
}: {
  setNavElementCallback: Function;
}) {
  return (
    <ProcessModelTreePage
      setNavElementCallback={setNavElementCallback}
      navigateToPage
    />
  );
}
