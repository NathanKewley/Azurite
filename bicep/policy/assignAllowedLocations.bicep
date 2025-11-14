targetScope = 'subscription'

param policyDisplayName string
param policyAssignmentName string
param enforcementMode string
param allowedLocations array

resource assignment 'Microsoft.Authorization/policyAssignments@2019-09-01' = {
    name: policyAssignmentName
    scope: subscription()
    properties: {
        displayName: policyDisplayName
        policyDefinitionId: '/providers/Microsoft.Authorization/policyDefinitions/e56962a6-4747-49cd-b67b-bf8b01975c4c'
        enforcementMode: enforcementMode
        parameters: {
            listOfAllowedLocations: {
                value: allowedLocations
            }
        }
    }
}

output assignmentId string = assignment.id
