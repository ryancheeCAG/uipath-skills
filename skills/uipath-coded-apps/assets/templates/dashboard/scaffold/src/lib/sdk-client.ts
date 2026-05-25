import { UiPath } from '@uipath/uipath-typescript/core'
import { Jobs } from '@uipath/uipath-typescript/jobs'
import { QueueItems } from '@uipath/uipath-typescript/queues'
import { Tasks } from '@uipath/uipath-typescript/tasks'
import { Entities } from '@uipath/uipath-typescript/entities'

export function createSdkServices(sdk: UiPath) {
  return {
    jobs:       new Jobs(sdk),
    queueItems: new QueueItems(sdk),
    tasks:      new Tasks(sdk),
    entities:   new Entities(sdk),
  }
}
