#!/usr/bin/env python3
"""
Integration test for GitLab integration against live instance.

This test hits a real GitLab API endpoint to verify the GitLabClient works correctly.
Unlike tests/test_gitlab.py (which uses mocks), this requires actual credentials and a real project.

Usage:
    python integration-tests/test_gitlab_live.py --token <gitlab-token> --project-url <project-url>

Example:
    python integration-tests/test_gitlab_live.py --token glpat-xxxxxxxxxxxx --project-url https://gitlab.com/mygroup/myproject

This script will:
1. Connect to the GitLab project
2. List recent pipelines
3. Get jobs for the latest pipeline
4. Download logs for a job
5. Check pipeline and job status
"""

import argparse
import sys
from pathlib import Path
from datetime import datetime

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from git_maestro.gitlab import GitLabClient, parse_gitlab_url


def push_test_files_to_project(project, test_project_dir: Path):
    """
    Push test-project files to the GitLab project to trigger pipelines.

    Args:
        project: GitLab project object
        test_project_dir: Path to test-project directory
    """
    print("\n" + "=" * 60)
    print("Pushing test files to project...")
    print("=" * 60)

    try:
        # Files to push
        files_to_push = [
            (".gitlab-ci.yml", test_project_dir / ".gitlab-ci.yml"),
            ("src/hello.py", test_project_dir / "src" / "hello.py"),
            ("tests/test_hello.py", test_project_dir / "tests" / "test_hello.py"),
        ]

        actions = []
        for file_path, local_path in files_to_push:
            if local_path.exists():
                content = local_path.read_text()
                actions.append(
                    {
                        "action": "create",
                        "file_path": file_path,
                        "content": content,
                    }
                )
                print(f"  Adding: {file_path}")
            else:
                print(f"  Warning: {local_path} not found, skipping")

        if not actions:
            print("✗ No files to push")
            return False

        # Create a commit with all files
        commit = project.commits.create(
            {
                "branch": "main",
                "commit_message": "Add test files and CI/CD configuration",
                "actions": actions,
            }
        )

        print(f"\n✓ Pushed {len(actions)} files in commit {commit.short_id}")
        print(f"  Commit URL: {commit.web_url}")
        print("\n  This should trigger a GitLab CI/CD pipeline!")

        return True

    except Exception as e:
        print(f"✗ Error pushing files: {e}")
        return False


def create_test_project(token: str, namespace_path: str, project_name: str):
    """
    Create a test project on GitLab.

    Args:
        token: GitLab personal access token
        namespace_path: Group/namespace path (e.g., 'test9863202')
        project_name: Project name (e.g., 'git-maestro-test-20260113-003845')

    Returns:
        Tuple of (project_url, gitlab_connection, project_object) or (None, None, None) on error
    """
    try:
        import gitlab

        print(f"Creating test project: {namespace_path}/{project_name}")

        gl = gitlab.Gitlab("https://gitlab.com", private_token=token)
        gl.auth()

        # Try to find the namespace
        try:
            # First try as group ID (numeric)
            try:
                namespace_id = int(namespace_path)
                namespace = gl.groups.get(namespace_id)
            except ValueError:
                # Not numeric, try as path
                groups = gl.groups.list(search=namespace_path)
                matching_groups = [
                    g
                    for g in groups
                    if g.path == namespace_path or g.full_path == namespace_path
                ]
                if not matching_groups:
                    print(f"Error: Could not find namespace '{namespace_path}'")
                    print("\nAvailable namespaces you have access to:")
                    user_groups = gl.groups.list(owned=True)
                    for g in user_groups:
                        print(f"  - {g.full_path} (ID: {g.id})")
                    return None, None, None
                namespace = matching_groups[0]
        except gitlab.exceptions.GitlabGetError as e:
            print(f"Error: Could not access namespace '{namespace_path}': {e}")
            return None, None, None

        print(f"Found namespace: {namespace.full_path} (ID: {namespace.id})")

        # Create the project
        project_data = {
            "name": project_name,
            "namespace_id": namespace.id,
            "description": f"Integration test project created at {datetime.now().isoformat()}",
            "visibility": "public",
            "initialize_with_readme": True,  # Add a README so there's an initial commit
        }

        project = gl.projects.create(project_data)

        print(f"✓ Project created: {project.web_url}")
        print(f"  Project ID: {project.id}")
        print(f"  Path: {project.path_with_namespace}")

        return f"https://gitlab.com/{project.path_with_namespace}", gl, project

    except Exception as e:
        print(f"Error creating project: {e}")
        return None, None, None


def main():
    parser = argparse.ArgumentParser(
        description="Integration test for GitLab against a live instance",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Test with explicit token
  python integration-tests/test_gitlab_live.py --token glpat-xxxxxxxxxxxx --project-url https://gitlab.com/mygroup/myproject

  # Use token from config file
  python integration-tests/test_gitlab_live.py --project-url https://gitlab.com/mygroup/myproject
        """,
    )

    parser.add_argument(
        "--token",
        help="GitLab personal access token (if not provided, reads from ~/.config/git-maestro/tokens.conf)",
        default=None,
    )

    parser.add_argument(
        "--project-url",
        required=True,
        help="GitLab project URL (e.g., https://gitlab.com/group/project)",
    )

    args = parser.parse_args()

    token = args.token
    project_url = args.project_url

    # If token not provided, try to read from config
    if not token:
        config_file = Path.home() / ".config" / "git-maestro" / "tokens.conf"
        if config_file.exists():
            try:
                with open(config_file, "r") as f:
                    for line in f:
                        if line.startswith("gitlab="):
                            token = line.split("=", 1)[1].strip()
                            print(
                                "Using token from config file: ~/.config/git-maestro/tokens.conf\n"
                            )
                            break
            except Exception as e:
                print(f"Warning: Could not read config file: {e}")

        if not token:
            print("Error: No token provided and none found in config file")
            print("\nPlease either:")
            print("  1. Provide --token argument")
            print("  2. Set up token in ~/.config/git-maestro/tokens.conf")
            print("     (add line: gitlab=YOUR_TOKEN)")
            sys.exit(1)

    # Generate unique project URL with timestamp
    parsed = parse_gitlab_url(project_url)
    if not parsed:
        print(f"Error: Could not parse project URL: {project_url}")
        sys.exit(1)

    # Extract namespace and project name, add timestamp
    project_path_parts = parsed["project_path"].split("/")
    if len(project_path_parts) < 2:
        print(
            f"Error: Invalid project path format. Expected 'namespace/project', got: {parsed['project_path']}"
        )
        sys.exit(1)

    namespace_path = "/".join(project_path_parts[:-1])
    base_project_name = project_path_parts[-1]

    # Add timestamp to make it unique
    timestamp = datetime.now().strftime("%Y%m%d-%H%M%S")
    unique_project_name = f"{base_project_name}-{timestamp}"

    # Construct new URL with unique project name
    unique_project_url = (
        f"https://{parsed['host']}/{namespace_path}/{unique_project_name}"
    )

    print("Testing GitLab integration")
    print(f"  Namespace: {namespace_path}")
    print(f"  Project: {unique_project_name}")
    print(f"  URL: {unique_project_url}\n")

    # Test 1: Parse URL
    print("=" * 60)
    print("Test 1: Parse GitLab URL")
    print("=" * 60)
    parsed_unique = parse_gitlab_url(unique_project_url)
    if parsed_unique:
        print("✓ URL parsed successfully")
        print(f"  Host: {parsed_unique['host']}")
        print(f"  Project path: {parsed_unique['project_path']}")
        print(f"  Encoded path: {parsed_unique['project_path_encoded']}")
    else:
        print("✗ Failed to parse URL")
        sys.exit(1)

    # Test 2: Initialize client (create project if needed)
    print("\n" + "=" * 60)
    print("Test 2: Initialize GitLab Client")
    print("=" * 60)

    client = None
    project_was_created = False
    try:
        client = GitLabClient(unique_project_url, token)
        print("✓ Client initialized successfully")
        print(f"  Project: {client.project.name}")
        print(f"  Project ID: {client.project.id}")
        print(f"  Web URL: {client.project.web_url}")
    except Exception as e:
        error_msg = str(e)
        if "404" in error_msg or "Not Found" in error_msg:
            print("Project does not exist, creating it...")
            print("")

            # Create the project
            created_url, gl_conn, created_project = create_test_project(
                token, namespace_path, unique_project_name
            )
            if not created_url:
                print("✗ Failed to create project")
                sys.exit(1)

            project_was_created = True

            # Push test-project files to trigger pipelines
            script_dir = Path(__file__).parent
            test_project_dir = script_dir.parent / "test-project"

            if test_project_dir.exists():
                push_success = push_test_files_to_project(
                    created_project, test_project_dir
                )
                if push_success:
                    # Wait for pipeline to start
                    import time

                    print("\nWaiting for pipeline to start...")
                    time.sleep(10)  # Give GitLab time to trigger the pipeline
                else:
                    print(
                        "\n[Warning] Could not push test files, pipeline tests may fail"
                    )
            else:
                print(
                    f"\n[Warning] test-project directory not found at {test_project_dir}"
                )
                print("Pipeline tests will not have any pipelines to test against.")

            # Use the created project object directly with GitLabClient
            print("\n" + "=" * 60)
            print("Test 2 (using created project): Initialize GitLab Client")
            print("=" * 60)
            try:
                # Initialize the client with the created project
                client = GitLabClient.__new__(GitLabClient)
                client.host = parsed_unique["host"]
                client.project_path = parsed_unique["project_path"]
                client.project_path_encoded = parsed_unique["project_path_encoded"]
                client.gl = gl_conn
                client.project = created_project

                print("✓ Client initialized successfully with created project")
                print(f"  Project: {client.project.name}")
                print(f"  Project ID: {client.project.id}")
                print(f"  Web URL: {client.project.web_url}")
            except Exception as e2:
                print(f"✗ Failed to initialize client with created project: {e2}")
                sys.exit(1)
        else:
            print(f"✗ Failed to initialize client: {e}")
            sys.exit(1)

    if not client:
        print("✗ Client initialization failed")
        sys.exit(1)

    # Test 3: Get pipelines
    print("\n" + "=" * 60)
    print("Test 3: Get Recent Pipelines")
    print("=" * 60)
    try:
        pipelines = client.get_pipelines(per_page=5)
        print(f"✓ Retrieved {len(pipelines)} pipelines")

        if pipelines:
            for i, pipeline in enumerate(pipelines, 1):
                print(f"\n  Pipeline {i}:")
                print(f"    ID: {pipeline.id}")
                print(f"    Status: {pipeline.status}")
                print(f"    Ref: {pipeline.ref}")
                print(f"    SHA: {pipeline.sha[:8]}")
                print(f"    Created: {pipeline.created_at}")
                # Duration may not be available from list(), only from get()
                if hasattr(pipeline, "duration") and pipeline.duration:
                    print(f"    Duration: {pipeline.duration}s")
                print(f"    URL: {pipeline.web_url}")
        else:
            print("  No pipelines found")
            if project_was_created:
                print("\n  Note: Project was just created and CI/CD files were pushed.")
                print(
                    "  The pipeline might still be starting, or there may have been an issue."
                )
                print("  Check the project URL to see if a pipeline appears:")
                print(f"    {client.project.web_url}/-/pipelines")
                print(
                    "\n  If you wait a bit and re-run this test, the pipeline should appear."
                )
            else:
                print("\n  Note: No pipelines exist in this project.")
                print("  Add a .gitlab-ci.yml file and push to trigger a pipeline.")
            print("\n  Basic client functionality has been verified.")
            return 0

    except Exception as e:
        print(f"✗ Failed to get pipelines: {e}")
        return 1

    # Test 4: Get pipeline details
    if pipelines:
        latest_pipeline = pipelines[0]
        print("\n" + "=" * 60)
        print(f"Test 4: Get Pipeline Details (ID: {latest_pipeline.id})")
        print("=" * 60)
        try:
            pipeline = client.get_pipeline(latest_pipeline.id)
            print("✓ Retrieved pipeline details")
            print(f"  Status: {pipeline.status}")
            print(f"  Ref: {pipeline.ref}")
            print(f"  User: {pipeline.user['username'] if pipeline.user else 'N/A'}")
        except Exception as e:
            print(f"✗ Failed to get pipeline details: {e}")

        # Test 5: Get jobs
        print("\n" + "=" * 60)
        print(f"Test 5: Get Pipeline Jobs (Pipeline ID: {latest_pipeline.id})")
        print("=" * 60)
        try:
            jobs = client.get_pipeline_jobs(latest_pipeline.id)
            print(f"✓ Retrieved {len(jobs)} jobs")

            if jobs:
                for i, job in enumerate(jobs, 1):
                    print(f"\n  Job {i}:")
                    print(f"    ID: {job.id}")
                    print(f"    Name: {job.name}")
                    print(f"    Stage: {job.stage}")
                    print(f"    Status: {job.status}")
                    if job.duration:
                        print(f"    Duration: {job.duration}s")
                    print(f"    URL: {job.web_url}")
                    if hasattr(job, "failure_reason") and job.failure_reason:
                        print(f"    Failure reason: {job.failure_reason}")

                # Test 6: Download job log
                first_job = jobs[0]
                print("\n" + "=" * 60)
                print(f"Test 6: Download Job Log (Job ID: {first_job.id})")
                print("=" * 60)
                try:
                    log_dir = Path("/tmp/gitlab-test-logs")
                    log_dir.mkdir(parents=True, exist_ok=True)
                    log_file = log_dir / f"job-{first_job.id}.log"

                    success = client.download_job_log(first_job.id, log_file)
                    if success:
                        log_size = log_file.stat().st_size
                        print("✓ Downloaded job log")
                        print(f"  Location: {log_file}")
                        print(f"  Size: {log_size} bytes")

                        # Show first few lines
                        with open(log_file, "r") as f:
                            lines = f.readlines()[:5]
                            if lines:
                                print("\n  First few lines:")
                                for line in lines:
                                    print(f"    {line.rstrip()}")
                    else:
                        print("✗ Failed to download job log")
                except Exception as e:
                    print(f"✗ Error downloading job log: {e}")

                # Test 7: Check job status
                print("\n" + "=" * 60)
                print(f"Test 7: Check Job Status (Job ID: {first_job.id})")
                print("=" * 60)
                try:
                    status = client.get_job_status(first_job.id)
                    print("✓ Retrieved job status")
                    print(f"  Status: {status['status']}")
                    print(f"  Stage: {status['stage']}")
                    print(f"  Name: {status['name']}")
                    if status.get("failure_reason"):
                        print(f"  Failure reason: {status['failure_reason']}")
                except Exception as e:
                    print(f"✗ Error checking job status: {e}")

            else:
                print("  No jobs found for this pipeline")

        except Exception as e:
            print(f"✗ Failed to get jobs: {e}")

        # Test 8: Get failed jobs
        print("\n" + "=" * 60)
        print(f"Test 8: Get Failed Jobs (Pipeline ID: {latest_pipeline.id})")
        print("=" * 60)
        try:
            failed_jobs = client.get_failed_jobs(latest_pipeline.id)
            print(f"✓ Retrieved {len(failed_jobs)} failed jobs")

            if failed_jobs:
                for i, job in enumerate(failed_jobs, 1):
                    print(f"\n  Failed Job {i}:")
                    print(f"    ID: {job['id']}")
                    print(f"    Name: {job['name']}")
                    print(f"    Stage: {job['stage']}")
                    print(f"    Status: {job['status']}")
                    print(f"    URL: {job['web_url']}")
                    if job.get("failure_reason"):
                        print(f"    Failure reason: {job['failure_reason']}")
            else:
                print("  No failed jobs (all jobs successful or none exist)")

        except Exception as e:
            print(f"✗ Failed to get failed jobs: {e}")

        # Test 9: Check pipeline status
        print("\n" + "=" * 60)
        print(f"Test 9: Check Pipeline Status (Pipeline ID: {latest_pipeline.id})")
        print("=" * 60)
        try:
            status = client.get_pipeline_status(latest_pipeline.id)
            print("✓ Retrieved pipeline status")
            print(f"  Status: {status['status']}")
            print(f"  Ref: {status['ref']}")
            print(f"  SHA: {status['sha'][:8]}")
            print(f"  Created: {status['created_at']}")
            print(f"  Updated: {status['updated_at']}")
        except Exception as e:
            print(f"✗ Error checking pipeline status: {e}")

    print("\n" + "=" * 60)
    print("All tests completed!")
    print("=" * 60)
    return 0


if __name__ == "__main__":
    sys.exit(main())
