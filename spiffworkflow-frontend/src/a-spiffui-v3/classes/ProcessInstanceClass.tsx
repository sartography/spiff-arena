export default class ProcessInstanceClass {
  static terminalStatuses() {
    return ['complete', 'error', 'terminated'];
  }

  static nonErrorTerminalStatuses() {
    return ['complete', 'terminated'];
  }
}
