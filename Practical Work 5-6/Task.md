# Cloud Computing · Practical Works 5–6

## Design and Build Your Own SaaS

You will design a small software service, build it, and demonstrate how two independent customer organisations can use the same running application. Run the entire project on a local machine or Linux VM with Docker. Use synthetic data. Choose your own topic, language, framework and storage. A web interface or an HTTP API is sufficient.

## Practical Work 5 · Design the service

1. Describe your idea in 3–5 sentences. Identify the organisations that would use the service, the recurring problem it solves, and a feature or allowance a customer might pay for.
2. Describe one workflow from start to finish. For example, a studio publishes available slots and registers a booking. List the actions the prototype will support and the records it will store.
3. Draw a simple diagram showing both customer organisations, the shared application and its storage. In this project, a tenant is a customer organisation with its own data. Explain how the server identifies the tenant making a request and determines which records it can access.
4. Define two plans and one measurable limit that differs between them. State which action consumes the allowance, how the server checks it, and what response a customer receives at the limit.
5. Prepare three acceptance checks covering normal use, an attempted request for another tenant’s record, and the plan limit. For each check, state the starting conditions, the action and the expected result.

**Deliverable.** Submit a short design brief of approximately 1–2 pages with the diagram and acceptance checks. Use this design as the starting point for Practical Work 6.

## Practical Work 6 · Build and demonstrate the service

1. Implement the workflow from Practical Work 5. Set up two test tenants, A and B, and assign each a different plan. You may use two preconfigured API tokens or two test accounts. The server must derive the tenant from the verified token or session.
2. Store records with their tenant association and apply the access check to every implemented operation on tenant data. Both tenants must be able to carry out the workflow on their own data. A request made with A’s credentials for a record belonging to B must be rejected without exposing or changing B’s data.
3. Enforce the plan limit on the server. You may configure the plans in advance. A payment integration is outside the assignment scope.
4. Build your Docker image from source and run the service locally. Document how to build and start the application, how to initialise test data, and how to make requests as each tenant. Use test credentials in the instructions.
5. Run the checks below against the containerised application. Save requests and responses or screenshots, and record the actual results alongside the expected results.

| Check | What to demonstrate |
| --- | --- |
| Normal use | Both A and B complete the main workflow on their own data. |
| Tenant isolation | B creates a record and can access it. A uses its own credentials to request that same record and receives a rejection. Confirm that B’s record remains accessible to B and intact. |
| Plan limit | A can create resources up to its allowance. Its next attempt fails and the number of resources stays the same. B succeeds at the corresponding count under its higher allowance. |

**Deliverable.** Submit a link to your GitHub repository containing the source code, Dockerfile, and README with local build and run instructions. Submit the completed test results with evidence. Include the design brief from Practical Work 5 and briefly describe any changes you made during implementation.
