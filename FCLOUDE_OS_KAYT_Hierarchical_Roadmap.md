# FCLOUDE OS + KAYT — Hierarchical Development Roadmap

**Document status:** Working execution roadmap  
**Source baseline:**  
1. `FCLOUDE_OS_KAYT_Master_Blueprint_v1.pdf` — Working Blueprint v1.0, 17 October 2026  
2. `FCLOUDE_KAYT_Architecture_Plan.md` — Chief Architect's Plan v1.0, 17 October 2026  
3. `fcloude_os_kayt_master_technical_research_protocol_report.md` — Master Technical Research Protocol Report  

**Purpose:** Turn the three project documents into a step-by-step sequence of goals, milestones, small tasks, and completion checks. This is an execution plan, not a claim that any milestone has already been completed.

---

## 0. How to Use This Roadmap

### Status key
- `[ ]` Not started
- `[-]` In progress
- `[x]` Done and checked
- `[!]` Blocked or needs a decision

### Rules for marking work complete
1. A milestone is complete only when its deliverable exists and its acceptance checks pass.
2. Do not skip a gate because a deadline has arrived. The Blueprint explicitly says to treat this as a sequence, not a deadline contract.
3. Learn the layer before building it. Reuse commodity infrastructure; build the differentiated experience and permission model.
4. Keep KAYT and FCLOUDE OS as **two tracks**: build KAYT first; customize the Linux image only after KAYT works.
5. Keep the first version narrow: one useful workflow, explicit user-selected input, visible provider, safe errors, and default-deny permissions.
6. Do not add features simply because they sound impressive. If a feature does not serve the current milestone, put it in `docs/future-ideas.md` and return to the current gate.
7. Before relying on a third-party tool, confirm its current official repository, maintenance status, license, compatibility, and relevant security notes. The source documents explicitly flag several research claims for re-verification.
8. Use the current project documents as the decision baseline. If implementation reveals a contradiction, record it in `docs/decisions.md` and update this roadmap deliberately rather than silently changing direction.

### Product definition used throughout
> **KAYT is a transparent, default-deny assistant that reads only the file the user picked, explains what it will do, and cannot do anything else.**

### Scope boundaries for the first version
**Build:** KAYT core and user experience, model-provider adapter, session-only file grants, strict structured-output validation, deterministic policy engine, narrow tool gateway, minimal audit log, and basic tests.

**Reuse:** upstream Linux kernel and drivers, Ubuntu base packages and updates, default GNOME initially, existing OS accounts, Git, Python, a supported ISO-customization tool later, and a model runtime such as Ollama only after the mock-provider path works.

**Do not build in the MVP:** custom kernel, custom package manager, custom language/compiler, custom updater, telemetry, biometrics, always-on voice, autonomous terminal, arbitrary shell execution, administrator/root access, arbitrary file search, or multi-agent orchestration.

---

# TRACK A — KAYT (Build This First)

## GOAL 1 — Establish a Safe, Reproducible Development Environment

**Goal outcome:** A private project repository and one recoverable Linux virtual machine are ready. The user can locate project files, use Git, and restore the VM to a known-good state.

### Milestone 1.1 — Confirm project boundaries and decisions
- [ ] Read the product definition and non-goals in the Master Blueprint.
- [ ] Read the two-track decision in the Architecture Plan: KAYT first; FCLOUDE OS later.
- [ ] Create a short `docs/decisions.md`.
- [ ] Record the initial decision: “KAYT is built separately from the OS customization.”
- [ ] Record the initial base-system proposal from the documents: Ubuntu 24.04 LTS for learning/development, with version and compatibility to be re-verified before ISO work.
- [ ] Record the initial language choice: Python.
- [ ] Record the initial model strategy: mock provider first; one real provider later.
- [ ] Record deferred features so they do not silently enter the MVP.

**Deliverable:** `docs/decisions.md`  
**Gate:** The product scope and first implementation path are written down.

### Milestone 1.2 — Create the private repository
- [ ] Create a **private** GitHub repository named `fcloude-kayt`.
- [ ] Add `README.md` describing the project and its narrow MVP.
- [ ] Add `.gitignore` entries for Python caches, virtual environments, `.env`, local logs, VM disk files, and model-weight files.
- [ ] Add `SECURITY.md` with a basic way to report a vulnerability.
- [ ] Choose a license only after reviewing the intended project and dependency licensing; the Architecture Plan leaves MIT vs Apache-2.0 as a decision, not a settled fact.
- [ ] Do not commit API keys, passwords, personal documents, VM images, or model weights.
- [ ] Make the first commit and confirm it appears in the private repository.

**Deliverable:** Private `fcloude-kayt` repository with baseline files.  
**Gate:** Repository is usable and contains no secrets or large machine/model artifacts.

### Milestone 1.3 — Prepare one Linux VM
- [ ] Keep Windows 11 as the host system.
- [ ] Install/use VirtualBox rather than installing a prototype directly over Windows or repartitioning the laptop.
- [ ] Download the selected Ubuntu image from its official source.
- [ ] Before choosing the image for long-term use, verify current support status and VirtualBox compatibility.
- [ ] Create one Ubuntu VM with modest resources; the Architecture Plan suggests approximately 4 GB RAM and 2 CPUs as a starting point.
- [ ] Complete first boot and user setup.
- [ ] Install available updates.
- [ ] Confirm networking works.
- [ ] Take a VM snapshot named `clean-install`.
- [ ] Test that the snapshot can be restored.

**Deliverable:** Working Ubuntu VM and tested `clean-install` snapshot.  
**Gate:** You can recover the VM without rebuilding it from scratch.

### Milestone 1.4 — Learn the minimum Linux and Git skills
- [ ] Practise navigation and file operations: `pwd`, `ls`, `cd`, `mkdir`, `cp`, `mv`, `cat`, `grep`, and `find`.
- [ ] Practise inspecting permissions with `ls -l` and changing a test file's permissions with `chmod`.
- [ ] Practise inspecting processes with `ps` and `top`.
- [ ] Learn how to inspect installed packages and updates using Ubuntu's package-management tools.
- [ ] Practise `git status`, `git add`, `git commit`, `git diff`, and `git log`.
- [ ] Create a tiny text file, change it, inspect the diff, commit it, and view the history.
- [ ] Write down commands or concepts you cannot yet explain.

**Deliverable:** `docs/linux-git-notes.md` or equivalent notes.  
**Gate:** You can explain where files live, what permissions mean, how to inspect a process, and how to inspect a Git change.

### GOAL 1 — FINAL RECHECK
- [ ] The repository is private and contains the expected baseline files.
- [ ] No secrets, VM disks, or model files are committed.
- [ ] Ubuntu boots, networking works, and updates can be checked.
- [ ] The `clean-install` snapshot has actually been restored successfully.
- [ ] The first decision is recorded in `docs/decisions.md`.
- [ ] Basic Linux and Git operations have been practised and can be explained.
- [ ] **Do not begin the next goal until these checks pass.**

---

## GOAL 2 — Create the Smallest Working KAYT Prototype with a Mock Provider

**Goal outcome:** A Python command-line prototype accepts a question and explicitly supplied text, sends it to a mock provider, and returns a predictable response without needing a paid API or a local model.

### Milestone 2.1 — Set up the Python project
- [ ] Install/use a supported Python version available in the development environment.
- [ ] Create a project virtual environment.
- [ ] Learn and use Python variables, functions, modules, exceptions, file handling, and JSON.
- [ ] Add `pyproject.toml` with the minimum project metadata and dependencies.
- [ ] Create the package directory `src/kayt/`.
- [ ] Create the initial entry point `src/kayt/cli.py`.
- [ ] Add a simple test command using `unittest` or `pytest`; start with the simpler option and avoid unnecessary frameworks.

**Deliverable:** A runnable Python package skeleton.  
**Gate:** The project runs in its virtual environment and can run a basic test.

### Milestone 2.2 — Define the first narrow user workflow
- [ ] Implement text input from the user.
- [ ] Implement a user-selected or explicitly supplied supported text-file input.
- [ ] Display which input KAYT is about to use.
- [ ] Display the active provider name (`mock` at this stage).
- [ ] Return a summary or explanation.
- [ ] Add a clear way to end the session.
- [ ] Keep all interaction local for the mock-provider milestone.
- [ ] Show understandable error messages for missing, unsupported, or empty input.

**Deliverable:** End-to-end CLI workflow using a mock response.  
**Gate:** The workflow works without Ollama, a remote API, or an API key.

### Milestone 2.3 — Define the provider adapter
- [ ] Create a small provider interface with one predictable input/output contract.
- [ ] Implement `MockProvider` using fixed/deterministic responses.
- [ ] Keep provider-specific details out of the core workflow.
- [ ] Add tests proving the core can call the mock provider.
- [ ] Ensure provider changes will not require rewriting policy or permission code.
- [ ] Document how a future provider will implement the same interface.

**Deliverable:** Mock provider plus documented provider contract.  
**Gate:** The core depends on the adapter interface, not on a particular model runtime.

### Milestone 2.4 — Handle input limits and failures
- [ ] Set a conservative maximum file size for the prototype.
- [ ] Reject unsupported file types.
- [ ] Handle unreadable files and invalid text safely.
- [ ] Handle empty user prompts and empty files.
- [ ] Handle provider errors without exposing stack traces as normal user output.
- [ ] Ensure an error does not trigger a fallback to a more powerful or less restricted action.
- [ ] Add tests for each expected failure.

**Deliverable:** Basic input validation and error handling.  
**Gate:** Invalid inputs fail clearly and safely.

### GOAL 2 — FINAL RECHECK
- [ ] KAYT starts from the documented command.
- [ ] User text and a supported text file can be supplied.
- [ ] The mock provider returns a predictable response.
- [ ] The provider is clearly shown as `mock`.
- [ ] The workflow needs no paid API or local model.
- [ ] Oversized, unsupported, empty, unreadable, and invalid inputs fail safely.
- [ ] Tests pass from a clean checkout/virtual environment.
- [ ] **Do not add real-model complexity until the mock workflow is reliable.**

---

## GOAL 3 — Implement KAYT's Permission Boundary and Security Tests

**Goal outcome:** KAYT's permissions are enforced by deterministic Python code, not by trusting model output. The model cannot choose arbitrary paths or invoke a shell.

### Milestone 3.1 — Write the threat model before adding tools
- [ ] Create `docs/threat-model.md`.
- [ ] List untrusted inputs: selected-file text, model output, and any network-provided content.
- [ ] List trusted components: KAYT's Python policy code and operating-system permissions.
- [ ] Record the risk of prompt injection inside a document.
- [ ] Record the risk of malformed or unexpected model output.
- [ ] Record path traversal and unauthorized file access as threats.
- [ ] Record accidental logging of sensitive file contents as a threat.
- [ ] Define the response to unexpected behavior as **deny/fail closed**.
- [ ] Keep the application running as a normal user, never root.

**Deliverable:** `docs/threat-model.md`.  
**Gate:** The main trust boundaries and refusal behavior are documented before implementation.

### Milestone 3.2 — Implement session-only file grants
- [ ] Create `src/kayt/grants.py`.
- [ ] Let the user choose the file through the application workflow.
- [ ] Validate supported file type and size before granting access.
- [ ] Resolve and store the selected file reference inside an internal Grant record.
- [ ] Give each grant an opaque, session-only identifier such as `grant_1`.
- [ ] Store only the minimum information needed, such as resolved file reference, size, and grant ID.
- [ ] Make grants expire when the session ends.
- [ ] Ensure model output can reference a grant ID but cannot supply a filesystem path.
- [ ] Reject unknown, expired, or invented grant IDs.
- [ ] Do not rely on `realpath` alone as the security boundary.

**Deliverable:** Session-only grant system.  
**Gate:** A task can read only the resource explicitly granted by the user.

### Milestone 3.3 — Define strict structured output
- [ ] Create `src/kayt/schema.py`.
- [ ] Define the exact permitted JSON shape for a proposed operation.
- [ ] Define the allowed tool name(s), initially only a narrow operation such as `summarize_text`.
- [ ] Require a valid grant ID where relevant.
- [ ] Reject unknown fields and unexpected field types.
- [ ] Reject malformed JSON.
- [ ] Reject arbitrary paths, shell commands, and unrecognized tool names.
- [ ] Add positive tests for valid output and negative tests for malformed or extra fields.

**Deliverable:** Strict output schema and tests.  
**Gate:** Unexpected model output is rejected rather than interpreted loosely.

### Milestone 3.4 — Implement default-deny policy
- [ ] Create `src/kayt/policy.py`.
- [ ] Make the policy engine independent of the model provider.
- [ ] Allow only explicitly registered operations.
- [ ] Check that the requested tool is on the allowlist.
- [ ] Check that the grant exists and is valid for the current session.
- [ ] Deny every unknown tool, missing grant, invalid grant, and unexpected condition.
- [ ] Ensure model output can never change policy rules or grant itself permissions.
- [ ] Add negative tests proving dangerous/unrecognized requests are denied.

**Deliverable:** Deterministic policy engine.  
**Gate:** The default result for any unrecognized case is denial.

### Milestone 3.5 — Build the narrow tool gateway
- [ ] Create `src/kayt/tools.py` and the smallest gateway needed to call approved tools.
- [ ] Implement only the narrow operation needed by the MVP.
- [ ] Make the gateway re-check the policy at execution time.
- [ ] Do not implement arbitrary shell execution.
- [ ] Do not add root/admin access.
- [ ] Keep the tool's input limited to validated fields and grant IDs.
- [ ] Return structured success/failure results.
- [ ] Ensure the UI's confirmation, if any, is not treated as a replacement for backend enforcement.

**Deliverable:** Minimal allowlisted gateway.  
**Gate:** The operation cannot execute unless the backend policy approves it immediately before execution.

### Milestone 3.6 — Add a minimal audit log
- [ ] Create `src/kayt/audit.py`.
- [ ] Use a simple local JSON Lines log for prototype events.
- [ ] Record timestamp, task/action type, allow/deny decision, outcome, and relevant non-sensitive metadata.
- [ ] Do not log the selected file's contents.
- [ ] Avoid storing unnecessary prompts or sensitive data.
- [ ] Log denied requests and failures as well as successful actions.
- [ ] Document where the log is stored and how it can be cleared.
- [ ] Define a simple retention/clearing rule for the prototype.

**Deliverable:** Minimal audit log with privacy-conscious fields.  
**Gate:** Events can be inspected without the log becoming a copy of user files.

### Milestone 3.7 — Run adversarial and regression tests
- [ ] Test an unknown tool name.
- [ ] Test a missing grant ID.
- [ ] Test an invented grant ID.
- [ ] Test an expired grant.
- [ ] Test malformed JSON.
- [ ] Test unexpected JSON fields.
- [ ] Test a path-like string such as `../../etc/passwd` being supplied where a grant ID is expected.
- [ ] Test that prompt-injection text inside the selected file is treated as data, not policy.
- [ ] Test that provider failure does not bypass validation or policy.
- [ ] Test that a denied action is logged without recording file contents.
- [ ] Run the full test suite after each security-relevant change.
- [ ] Record the test results and any known limitations.

**Deliverable:** Security-focused tests and a recorded test report.  
**Gate:** All unauthorized-action tests fail safely. Passing these tests is not a security certification; it is the minimum project gate.

### GOAL 3 — FINAL RECHECK
- [ ] The threat model exists and matches the implemented design.
- [ ] The model never supplies an arbitrary filesystem path for the tool to open.
- [ ] Only user-created, session-only grants can identify readable files.
- [ ] Strict schema validation rejects malformed or unexpected output.
- [ ] The policy engine is deterministic, provider-independent, and default-deny.
- [ ] The gateway re-checks permission at execution time.
- [ ] No shell tool, arbitrary file search, root access, or admin action exists.
- [ ] Audit logs avoid file contents and include denied actions/failures.
- [ ] All negative security tests pass.
- [ ] **Do not integrate a real model until the permission boundary is tested.**

---

## GOAL 4 — Complete the KAYT MVP Experience

**Goal outcome:** A user can ask KAYT to explain or summarize a selected text file, understand what information is used and where it goes, see the provider, and clear the session.

### Milestone 4.1 — Connect the workflow end to end
- [ ] Connect CLI input to the KAYT core.
- [ ] Connect the core to the provider adapter.
- [ ] Connect structured output to schema validation.
- [ ] Connect validated requests to policy checks and the narrow gateway.
- [ ] Connect outcomes to the audit log.
- [ ] Surface the result and any errors clearly.
- [ ] Ensure the model's proposed action is never executed directly.

**Deliverable:** One end-to-end KAYT workflow.  
**Gate:** The workflow passes through every intended layer in the documented order.

### Milestone 4.2 — Make data use transparent
- [ ] Show the selected filename and file size before processing.
- [ ] Show the provider that will be used.
- [ ] State whether content stays local or will be sent to a remote service.
- [ ] For the mock provider, clearly indicate that no remote model is used.
- [ ] For any later remote provider, disclose the content that will be sent before the request.
- [ ] Do not imply that a local model is being used when the provider is remote.
- [ ] Make the current session easy to clear.

**Deliverable:** Clear data/provider notice and session-clear behavior.  
**Gate:** A user can tell what input is used, which provider is active, and whether content leaves the machine.

### Milestone 4.3 — Complete acceptance tests for the MVP
- [ ] Test a normal summary request.
- [ ] Test an explanation request.
- [ ] Test a file that is too large.
- [ ] Test an unsupported file.
- [ ] Test a missing/unreadable file.
- [ ] Test malformed provider output.
- [ ] Test a denied tool request.
- [ ] Test session clearing and grant expiration.
- [ ] Test that the displayed provider matches the provider actually called.
- [ ] Test that the app can be run from the documented instructions.

**Deliverable:** MVP acceptance-test checklist and results.  
**Gate:** Every P0 item from the Master Blueprint works: text input/output, selected-file input, provider adapter, input limits/errors, and permission allowlist.

### GOAL 4 — FINAL RECHECK
- [ ] KAYT solves one narrow end-to-end problem reliably.
- [ ] The user explicitly chooses the input file.
- [ ] KAYT explains what it will use before processing.
- [ ] Provider identity and local/remote handling are accurate.
- [ ] The session can be cleared.
- [ ] The core, schema, policy, gateway, and audit log are connected as documented.
- [ ] All P0 acceptance tests pass.
- [ ] Known limitations are documented.
- [ ] **Do not expand to system actions just because this milestone passes.**

---

## GOAL 5 — Add One Real Model Provider (Ollama First, If Practical)

**Goal outcome:** KAYT can use one real model provider through the same adapter, without changing the policy/security architecture. This goal is conditional on measured performance and current model/runtime licensing.

### Milestone 5.1 — Re-verify the provider and model
- [ ] Open the official Ollama documentation/repository before implementation.
- [ ] Verify current installation steps and API behavior for the target environment.
- [ ] Select a modest candidate model based on available RAM, disk space, and measured responsiveness.
- [ ] Read the model's license and usage restrictions; do not assume every model has the same terms.
- [ ] Confirm model downloads will not consume unreasonable disk space.
- [ ] Do not fork or rebuild Ollama unless a demonstrated requirement makes it necessary.
- [ ] Record the chosen runtime/model and verification date in project notes.

**Deliverable:** Provider decision note with links, version, model, license, and rationale.  
**Gate:** The choice is based on current primary sources, not assumptions.

### Milestone 5.2 — Implement the Ollama adapter
- [ ] Create a separate provider module for Ollama.
- [ ] Match the existing provider interface.
- [ ] Keep the mock provider available for tests.
- [ ] Configure the provider explicitly rather than silently switching providers.
- [ ] Handle runtime unavailable, model unavailable, timeout, and malformed response cases.
- [ ] Ensure provider errors cannot bypass schema validation, policy checks, grants, or the gateway.
- [ ] Show the active provider to the user.

**Deliverable:** Ollama provider adapter.  
**Gate:** The same KAYT core and policy tests run with either mock or Ollama.

### Milestone 5.3 — Benchmark on the actual laptop
- [ ] Record laptop/VM configuration used for the test.
- [ ] Measure cold-start time and time to first response.
- [ ] Measure completion time for a small, fixed test prompt.
- [ ] Record memory use and whether the VM/host becomes unresponsive.
- [ ] Repeat tests enough times to identify obvious variability.
- [ ] Test with the same fixed input so results can be compared.
- [ ] Define an acceptable response time for the prototype.
- [ ] If local inference is too slow, keep the mock provider for development and evaluate alternatives separately; do not compromise the permission architecture to gain speed.

**Deliverable:** `docs/provider-benchmark.md`.  
**Gate:** The local provider is retained only if measured performance is acceptable for the intended use.

### Milestone 5.4 — Re-run security tests with the real model
- [ ] Run all schema and policy tests.
- [ ] Test unexpected model output.
- [ ] Test prompt-injection content in a selected file.
- [ ] Test provider failure and timeout.
- [ ] Confirm no path or shell capability has been added.
- [ ] Confirm model output still cannot grant permissions.
- [ ] Confirm logs do not store file contents.

**Deliverable:** Updated provider/security test report.  
**Gate:** A real model does not weaken any previously passed security property.

### GOAL 5 — FINAL RECHECK
- [ ] Provider and model details were verified against current official sources.
- [ ] Model licensing was reviewed for the intended use.
- [ ] The adapter uses the same interface as the mock provider.
- [ ] The provider is visible and never silently misrepresented.
- [ ] Performance was measured on the actual machine.
- [ ] Failure modes are handled clearly.
- [ ] All security tests still pass.
- [ ] The mock provider remains available for fast, deterministic tests.
- [ ] **If local inference is not practical, document the result and continue with the architecture intact.**

---

## GOAL 6 — Add a Minimal Desktop Interface and Package KAYT

**Goal outcome:** Once CLI behavior and security tests are stable, KAYT can be launched as a normal user application in the Linux VM.

### Milestone 6.1 — Choose the smallest useful interface
- [ ] Review the working CLI and identify only the interactions a GUI must improve.
- [ ] Keep the first interface minimal: prompt, file selection, provider/data notice, response, error state, and clear-session action.
- [ ] Do not add voice, always-on listening, a complex dashboard, or multi-agent controls.
- [ ] Select a GUI toolkit only after checking the smallest suitable option and its dependencies.
- [ ] Record the decision and why the chosen toolkit is sufficient.

**Deliverable:** Minimal UI scope and toolkit decision.  
**Gate:** UI scope is limited to the proven MVP workflow.

### Milestone 6.2 — Implement the GUI around the existing core
- [ ] Build the file-selection interaction.
- [ ] Show the filename, size, and provider before processing.
- [ ] Show the local/remote data notice.
- [ ] Show progress and errors without hiding failures.
- [ ] Show the final response.
- [ ] Add a clear-session action that expires grants.
- [ ] Keep GUI code separate from policy decisions.
- [ ] Ensure the GUI cannot bypass backend permission checks.

**Deliverable:** Minimal desktop GUI.  
**Gate:** CLI and GUI use the same core, provider adapter, grants, schema, and policy.

### Milestone 6.3 — Package and launch as a normal user
- [ ] Define a repeatable installation/run procedure.
- [ ] Confirm KAYT launches without administrator/root privileges.
- [ ] Confirm required dependencies are documented.
- [ ] Test a fresh user/session.
- [ ] Test startup failure and missing-provider behavior.
- [ ] Document uninstall/removal steps for the prototype.

**Deliverable:** Repeatable KAYT package/run instructions.  
**Gate:** KAYT launches and fails safely on the Ubuntu VM as a normal user.

### GOAL 6 — FINAL RECHECK
- [ ] GUI contains only MVP interactions.
- [ ] GUI does not contain independent or weaker policy logic.
- [ ] File/provider/data information is visible before processing.
- [ ] Session clearing expires grants.
- [ ] KAYT runs as a normal user.
- [ ] Installation, launch, error, and removal instructions work from a clean VM snapshot.
- [ ] Security tests pass against the GUI path as well as the CLI path.
- [ ] **Only now is KAYT ready to be considered for inclusion in a custom OS image.**

---

# TRACK B — FCLOUDE OS (Start Only After KAYT Works)

## GOAL 7 — Prepare the Ubuntu-Based FCLOUDE OS Configuration

**Goal outcome:** A documented, repeatable list of base-system choices, installed applications, settings, and branding is ready before creating an ISO.

### Milestone 7.1 — Reconfirm the base system
- [ ] Re-check the current Ubuntu LTS release, support period, download source, and system requirements using official Ubuntu sources.
- [ ] Re-check compatibility with the chosen VirtualBox version and the later ISO-customization workflow.
- [ ] Re-check the current supported host distributions and target ISO compatibility for Cubic before relying on it.
- [ ] Decide whether to retain the proposed Ubuntu 24.04 LTS baseline or change it based on documented evidence.
- [ ] Record the decision, date, links, and compatibility rationale.
- [ ] Do not change base versions casually after packaging work begins.

**Deliverable:** `docs/base-distro-decision.md`.  
**Gate:** Base version and tool compatibility have been checked at the time of implementation.

### Milestone 7.2 — Define the first FCLOUDE OS experience
- [ ] Keep the existing desktop environment (default GNOME initially).
- [ ] List the small set of default applications required for the first image.
- [ ] Define which KAYT version will be included.
- [ ] Define basic FCLOUDE branding (name, wallpaper, icons/settings only where appropriate).
- [ ] Avoid replacing apt, the kernel, drivers, or the upstream update system.
- [ ] Avoid claiming that a customized Ubuntu image is an entirely independent distribution.
- [ ] Check relevant Ubuntu licensing and trademark requirements before public distribution.

**Deliverable:** `docs/fcloude-os-profile.md`.  
**Gate:** The image profile is small, transparent, and based on upstream components.

### Milestone 7.3 — Make configuration reproducible
- [ ] Record installed packages and their versions where practical.
- [ ] Record desktop settings and branding changes.
- [ ] Turn repeatable customizations into scripts/configuration where practical.
- [ ] Document manual changes that cannot yet be automated.
- [ ] Keep the configuration in Git.
- [ ] Record any dependency or licensing decisions.
- [ ] Ensure secrets and personal files are excluded from the image.

**Deliverable:** Version-controlled configuration notes/scripts.  
**Gate:** Another person can follow the documented process without guessing undocumented settings.

### GOAL 7 — FINAL RECHECK
- [ ] Base distro and ISO tool compatibility have been re-verified.
- [ ] The selected base version is recorded with rationale.
- [ ] The first desktop profile remains close to upstream.
- [ ] KAYT version and dependencies are documented.
- [ ] Branding/settings and package choices are reproducible.
- [ ] No personal files or secrets are included.
- [ ] Licensing and trademark checks are recorded before public distribution.
- [ ] **Do not build the ISO until the profile and KAYT package are stable.**

---

## GOAL 8 — Build the First FCLOUDE OS Test ISO

**Goal outcome:** A bootable, clearly labelled customized Ubuntu test image includes KAYT and the documented configuration.

### Milestone 8.1 — Prepare a clean ISO-building environment
- [ ] Take a snapshot of the known-good development VM.
- [ ] Follow the official Cubic project instructions for a compatible environment.
- [ ] Download the chosen base ISO from the official source and verify its integrity using the published method where available.
- [ ] Keep an untouched copy of the base ISO.
- [ ] Record tool versions and the build environment.
- [ ] Do not use the Windows host as an experimental installation target.

**Deliverable:** Documented ISO build environment.  
**Gate:** The build can be attempted again from a known state.

### Milestone 8.2 — Create the first customized image
- [ ] Open the base ISO in the verified ISO-customization workflow.
- [ ] Add the packaged KAYT application and its required dependencies.
- [ ] Apply only the settings listed in `docs/fcloude-os-profile.md`.
- [ ] Apply basic branding.
- [ ] Preserve the upstream package manager and update mechanism.
- [ ] Do not add a custom updater or custom package manager.
- [ ] Build an ISO and label it as an experimental/pre-release image.
- [ ] Record build steps, tool versions, and any manual changes.

**Deliverable:** First FCLOUDE OS test ISO.  
**Gate:** ISO build completes and the build procedure is documented.

### Milestone 8.3 — Boot and test in a clean VM
- [ ] Create a fresh test VM or restore a clean test snapshot.
- [ ] Boot the ISO without modifying the host system.
- [ ] Check that the desktop starts.
- [ ] Check display resolution/scaling.
- [ ] Check network access.
- [ ] Check sound where the VM supports it.
- [ ] Check suspend/resume if relevant to the VM environment.
- [ ] Launch KAYT as a normal user.
- [ ] Run the KAYT MVP acceptance tests.
- [ ] Test the package manager and available updates.
- [ ] Record every issue, expected/actual result, and severity.

**Deliverable:** `docs/iso-test-report.md`.  
**Gate:** The image boots and the essential desktop/KAYT/update checks pass in a clean VM.

### Milestone 8.4 — Rebuild reproducibly
- [ ] Rebuild the image from the documented inputs and configuration.
- [ ] Compare the resulting package/configuration state with the previous build.
- [ ] Record expected differences caused by timestamps or upstream package updates.
- [ ] Fix undocumented manual steps.
- [ ] Confirm the build procedure can be repeated without relying on memory.

**Deliverable:** Reproducible build notes and versioned image.  
**Gate:** The image can be rebuilt through documented steps and differences are understood.

### GOAL 8 — FINAL RECHECK
- [ ] ISO was built from a verified, documented base image.
- [ ] KAYT is included and launches as a normal user.
- [ ] The image boots in a clean VM.
- [ ] Network, display, sound, package updates, and other relevant VM checks are recorded.
- [ ] KAYT acceptance and security tests pass inside the image.
- [ ] No host installation or repartitioning was needed.
- [ ] Build steps and versions are documented.
- [ ] A rebuild was attempted and differences were recorded.
- [ ] The image is labelled experimental until preview gates are passed.

---

## GOAL 9 — Establish Release Readiness, Documentation, and a Limited Preview

**Goal outcome:** A small voluntary test group can evaluate the prototype with clear limitations, feedback channels, and a realistic maintenance plan.

### Milestone 9.1 — Review the product and security claims
- [ ] Describe the product accurately as a customized Ubuntu-based image unless and until a genuine distribution-level maintenance process exists.
- [ ] Document what KAYT can and cannot do.
- [ ] Document known bugs, limitations, and tested environments.
- [ ] State clearly that project testing is not independent security certification.
- [ ] Verify all third-party tool/model licenses for the actual distribution method.
- [ ] Review trademark/branding requirements before publishing.
- [ ] Run a secret scan on the repository and release artifacts.
- [ ] Ensure no private files, tokens, or sensitive logs are included.

**Deliverable:** Release-readiness review.  
**Gate:** Claims, licenses, and artifact contents have been reviewed before publication.

### Milestone 9.2 — Prepare user-facing documentation
- [ ] Update the main `README.md` with the project purpose and status.
- [ ] Document system requirements and tested environments.
- [ ] Document installation/boot instructions for the test image.
- [ ] Document how to launch and use KAYT.
- [ ] Explain provider choice and local/remote data handling.
- [ ] Document how to report bugs/security issues.
- [ ] Document how to recover from a failed test and how to remove the prototype.
- [ ] Keep a changelog or release notes for meaningful changes.

**Deliverable:** User-facing documentation set.  
**Gate:** A tester can follow the instructions without needing undocumented verbal guidance.

### Milestone 9.3 — Define maintenance and recovery basics
- [ ] Document how upstream Ubuntu updates are obtained and tested.
- [ ] Define how KAYT updates will be packaged for the prototype.
- [ ] Define a rollback/recovery approach for the VM test environment.
- [ ] Record who will monitor dependency and model-runtime changes.
- [ ] Avoid promising long-term support until the maintenance process is realistic.
- [ ] Define what would block a release (e.g. failing security tests, broken boot, unverified license).

**Deliverable:** `docs/maintenance-and-recovery.md`.  
**Gate:** The project has a basic plan for updates, recovery, and known release blockers.

### Milestone 9.4 — Conduct a limited voluntary preview
- [ ] Invite only a small group of willing testers.
- [ ] Tell testers the image is experimental and list known limitations.
- [ ] Give testers a feedback form or issue template.
- [ ] Ask testers to report installation/boot issues, confusing UX, and KAYT failures.
- [ ] Do not collect unnecessary personal data or add telemetry by default.
- [ ] Triage issues and record fixes.
- [ ] Re-run relevant tests after changes.

**Deliverable:** Preview feedback log and prioritized fixes.  
**Gate:** Feedback is reviewed and important release blockers are addressed before wider sharing.

### GOAL 9 — FINAL RECHECK
- [ ] Release claims accurately describe the project as it exists.
- [ ] License, trademark, and secret checks are complete.
- [ ] Documentation covers installation, use, data handling, limitations, bug reports, and recovery.
- [ ] Maintenance and update responsibilities are documented.
- [ ] A limited preview was voluntary and clearly labelled experimental.
- [ ] Feedback is recorded, prioritized, and followed by regression tests.
- [ ] No unsupported promise of long-term maintenance is made.
- [ ] **Only consider a wider release when the relevant gates pass.**

---

# FUTURE WORK — Explicitly Deferred

These are not required to complete the first KAYT MVP or first FCLOUDE OS test ISO. Revisit only after the core workflow is useful, stable, and tested.

- [ ] Additional model providers beyond the first working provider.
- [ ] More approved tools, each with its own threat analysis, allowlist entry, tests, confirmation behavior, and rollback story where feasible.
- [ ] File organization or other system-changing actions.
- [ ] Voice input/output.
- [ ] Multi-agent coordination.
- [ ] Advanced memory or persistent user profiles.
- [ ] Telemetry/analytics.
- [ ] Custom desktop shell or window manager.
- [ ] Custom update system or package manager.
- [ ] Custom kernel, compiler, or independent Linux-from-source distribution.
- [ ] Commercial distribution or broader public release.
- [ ] Any feature requiring broader privileges than the MVP.

**Rule:** Each future feature needs its own problem statement, threat analysis, design decision, tests, and acceptance checklist before implementation.

---

# Master Progress Dashboard

Use this table as the single overview. Update status only after completing each goal's final recheck.

| Goal | Target outcome | Status | Completion date | Notes / blockers |
|---|---|---|---|---|
| 1. Development environment | Private repo, recoverable Ubuntu VM, basic Linux/Git skills | [ ] | | |
| 2. Mock KAYT prototype | Working Python CLI and mock provider | [ ] | | |
| 3. Permission boundary | Grants, schema, default-deny policy, gateway, audit log, security tests | [ ] | | |
| 4. KAYT MVP experience | Transparent end-to-end selected-file workflow | [ ] | | |
| 5. Real provider | One provider adapter and measured performance, if practical | [ ] | | |
| 6. Minimal GUI/package | Normal-user desktop app using the same security core | [ ] | | |
| 7. OS configuration | Verified Ubuntu baseline and reproducible profile | [ ] | | |
| 8. Test ISO | Bootable image tested in a clean VM and rebuilt | [ ] | | |
| 9. Preview readiness | Documentation, maintenance/recovery, limited voluntary testing | [ ] | | |

---

# Final Operating Principles

1. **KAYT first; FCLOUDE OS second.**
2. **Reuse the kernel, drivers, desktop, package manager, and update system.**
3. **Build the KAYT experience and permission boundary yourself.**
4. **The model proposes; deterministic code decides.**
5. **The model never names a path; it can refer only to a user-created grant.**
6. **Default deny; fail closed.**
7. **No arbitrary shell, root access, or unrestricted system actions in the MVP.**
8. **Mock provider first; one real provider only after tests.**
9. **Benchmark on the actual machine rather than trusting estimates.**
10. **A customized ISO is not automatically an independent distribution.**
11. **If you cannot explain it, test it, and recover from it, do not merge or release it.**
12. **A gate passed beats a date met.**

---

## Source Traceability Notes

This roadmap is derived primarily from the three project documents listed at the top. The following structure preserves their key decisions:

- **Two-track strategy, product definition, build-vs-reuse, MVP features, tool stack, learning ladder, ISO progression, release gates:** Master Blueprint v1.0.
- **Python CLI first, mock provider, session-only grants, strict JSON schema, deterministic default-deny policy, gateway re-check, privacy-conscious JSONL audit log, repo layout, and security-focused tests:** Chief Architect's Plan v1.0.
- **Tool/provider research and research-verification discipline:** Master Technical Research Protocol Report, subject to the Architecture Plan's explicit warnings that selected links, licenses, repository identities, activity claims, and performance assumptions must be verified again before implementation.
- **Version-sensitive decisions:** Ubuntu release, Cubic compatibility, model/runtime versions, and licenses must be rechecked against official sources at the time the relevant milestone begins.

Where the source documents do not establish that a step has already been completed, this roadmap leaves it unchecked. This document is a plan, not evidence of completion or a security certification.
