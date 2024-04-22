import { useLocation } from 'react-router-dom';
import { SpiffTab } from '../interfaces';
import SpiffTabs from './SpiffTabs';

export default function TaskRouteTabs() {
  const location = useLocation();
  if (location.pathname.match(/^\/tasks\/\d+\/\b/)) {
    return null;
  }

  const spiffTabs: SpiffTab[] = [
    {
      path: '/tasks/in-progress',
      display_name: 'Em Andamento',
      tooltip: 'Visualizar Processos em andamento',
    },
    {
      path: '/tasks/completed-instances',
      display_name: 'Finalizado',
      tooltip: 'Visualizar Processos finalizados',
    },
    {
      path: '/tasks/create-new-instance',
      display_name: 'Novo Processo +',
      tooltip: 'Iniciar um Novo Processo',
    },
  ];
  return <SpiffTabs tabs={spiffTabs} />;
}
