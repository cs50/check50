import signal
from check50 import *

def main():
    signal.signal(signal.SIGINT, handler)

    # Parse command line arguments.
    parser = argparse.ArgumentParser()
    parser.add_argument("identifier", nargs=1)
    parser.add_argument("files", nargs="*")
    parser.add_argument("-d", "--debug",
                        action="store_true",
                        help="display machine-readable output")
    parser.add_argument("-l", "--local",
                        action="store_true",
                        help="run checks locally instead of uploading to cs50")
    parser.add_argument("--offline",
                        action="store_true",
                        help="run checks completely offline (implies --local)")
    parser.add_argument("--checkdir",
                        action="store",
                        default="~/.local/share/check50",
                        help="specify directory containing the checks "
                             "(~/.local/share/check50 by default)")
    parser.add_argument("--log",
                        action="store_true",
                        help="display more detailed information about check results")
    parser.add_argument("-v", "--verbose",
                        action="store_true",
                        help="display the full tracebacks of any errors")

    config.args = parser.parse_args()
    config.args.checkdir = os.path.abspath(os.path.expanduser(config.args.checkdir))
    identifier = config.args.identifier[0]
    files = config.args.files

    if config.args.offline:
        config.args.local = True

    if not config.args.local:
        try:

            # Submit to check50 repo.
            import submit50
        except ImportError:
            raise InternalError(
                "submit50 is not installed. Install submit50 and run check50 again.")
        else:
            submit50.handler.type = "check"
            signal.signal(signal.SIGINT, submit50.handler)

            submit50.run.verbose = config.args.verbose
            username, commit_hash = submit50.submit("check50", identifier)

            # Wait until payload comes back with check data.
            print("Checking...", end="")
            sys.stdout.flush()
            pings = 0
            while True:

                # Terminate if no response.
                if pings > 45:
                    print()
                    cprint("check50 is taking longer than normal!", "red", file=sys.stderr)
                    cprint("See https://cs50.me/checks/{} for more detail.".format(commit_hash),
                           "red", file=sys.stderr)
                    sys.exit(1)
                pings += 1

                # Query for check results.
                res = requests.post(
                    "https://cs50.me/check50/status/{}/{}".format(username, commit_hash))
                if res.status_code != 200:
                    continue
                payload = res.json()
                if payload["complete"]:
                    break
                print(".", end="")
                sys.stdout.flush()
                time.sleep(2)
            print()

            # Print results from payload.
            print_results(payload["checks"], config.args.log)
            print("See https://cs50.me/checks/{} for more detail.".format(commit_hash))
            sys.exit(0)

    # Copy all files to temporary directory.
    config.tempdir = tempfile.mkdtemp()
    src_dir = os.path.join(config.tempdir, "_")
    os.mkdir(src_dir)
    if len(files) == 0:
        files = os.listdir(".")
    for filename in files:
        copy(filename, src_dir)

    checks = import_checks(identifier)

    # Create and run the test suite.
    suite = unittest.TestSuite()
    for case in config.test_cases:
        suite.addTest(checks(case))
    result = TestResult()
    suite.run(result)
    cleanup()

    # Get list of results from TestResult class.
    results = result.results

    # Print the results.
    if config.args.debug:
        print_json(results)
    else:
        print_results(results, log=config.args.log)

main()
