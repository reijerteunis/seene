import { Controller, Get } from '@nestjs/common';
import { packageName } from '@seen/core';

/**
 * The liveness surface. It reports that this process is serving and which one it
 * is, and nothing else: a health check that touches the database turns a slow
 * query into an outage.
 */
@Controller('health')
export class HealthController {
  @Get()
  read(): { status: string; service: string; core: string } {
    return { status: 'ok', service: '@seen/api', core: packageName };
  }
}
