# Execute BASE PRP

Implement a feature using using the PRP file.

## PRP File: $ARGUMENTS

## Execution Process

1. **Load PRP**
   - Read the specified PRP file
   - Understand all context and requirements
   - Follow all instructions in the PRP and extend the research if needed
   - Ensure you have all needed context to implement the PRP fully
   - Do more web searches and codebase exploration as needed

2. **ULTRATHINK**
   - Think hard before you execute the plan. Create a comprehensive plan addressing all requirements.
   - Break down complex tasks into smaller, manageable steps using your todos tools.
   - Use the TodoWrite tool to create and track your implementation plan.
   - Identify implementation patterns from existing code to follow.

3. **Execute the plan**
   - Execute the PRP
   - Implement all the code

4. **Validate**
   - Run each validation command
   - Fix any failures
   - Re-run until all pass

5. **Complete**
   - Ensure all checklist items done
   - Run final validation suite
   - Report completion status
   - Read the PRP again to ensure you have implemented everything

6. **Create Completion Documentation**
   - Copy `PRPs/templates/prp_completion_template.md` to `PRPs/{feature-name}-completion.md`
   - Pre-populate with task name, PRP file path, and completion date
   - **Document Actual Implementation Results**:
     - Record what was actually implemented vs. what was planned
     - Document any deviations from the original PRP and reasons
     - List all files created, modified, or deleted
     - Note any discovered issues and how they were resolved
   - **Record All Testing Outcomes**:
     - Document actual test results (pass/fail counts, coverage percentages)
     - Include validation command outputs and any failures encountered
     - Record performance benchmarks if applicable
     - Document manual testing results and any issues found
   - **Fill Out Quality Verification Based on What Was Done**:
     - Only mark checkboxes for work that was actually completed
     - Provide specific evidence for each quality verification item
     - Document any quality standards that were not met and reasons
   - **Provide Specific TASK.md Update Content**:
     - Write the exact text to be added to TASK.md completion notes
     - Include discovered work items that weren't in original plan
     - Document performance results and any issues encountered
     - Provide clear completion status and next task dependencies
   - **Verify All Work Was Actually Completed**:
     - Cross-reference against PRP requirements to ensure nothing was missed
     - Document any incomplete items and reasons for deferral
     - Ensure all validation gates from the PRP were actually executed

7. **Reference the PRP**
   - You can always reference the PRP again if needed

Note: If validation fails, use error patterns in PRP to fix and retry.

## Automated Completion Template Creation
After successful PRP execution, the completion template ensures:
- Structured completion verification
- Mandatory TASK.md updates
- Quality verification checklist
- Next task dependency preparation
- Complete audit trail of work completed
