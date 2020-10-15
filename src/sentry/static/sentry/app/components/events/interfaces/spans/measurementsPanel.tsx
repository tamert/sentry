import React from 'react';
import styled from '@emotion/styled';

import {SentryTransactionEvent} from 'app/types';

import {getMeasurements} from './utils';

type Props = {
  event: SentryTransactionEvent;
};
class MeasurementsPanel extends React.PureComponent<Props> {
  render() {
    const {event} = this.props;

    const measurements = getMeasurements(event);

    console.log('measurements', measurements);

    return <Container>measurements</Container>;
  }
}

const Container = styled('div')`
  position: relative;
  flex-grow: 1;
  overflow: hidden;

  background-color: red;
`;

export default MeasurementsPanel;
