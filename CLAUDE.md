Run all tests like:

    cd [git_root] && ,/bin/run_pyl
    cd ~/projects/github/sartography/spiff-arena && ./bin/run_pyl

Run a single backend test like:

    cd [backend_dir] && poet [test_name]
    cd ~/projects/github/sartography/spiff-arena/spiffworkflow-backend && poet test_process_instance_list_filter

Or a single backend test file like:

    cd ~/projects/github/sartography/spiff-arena/spiffworkflow-backend && poet tests/spiffworkflow_backend/integration/test_process_model_milestones.py
