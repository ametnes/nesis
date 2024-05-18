import React, { useState } from 'react';
import { useHistory, Route, Switch, useRouteMatch } from 'react-router-dom';
import Nesis from '../../components/Menu';
import styled from 'styled-components/macro';
import { FileEarmarkPost } from 'react-bootstrap-icons';
import {
  Box,
  Container,
  IconButton,
  LinearProgress,
  Typography,
} from '@mui/material';

import { Formik, Form as FormikForm } from 'formik';
import { TextField } from '../../components/form';
import ChatBubbleIcon from '@mui/icons-material/ChatBubble';
import ChatBubbleOutlineIcon from '@mui/icons-material/ChatBubbleOutline';
import SendIcon from '@mui/icons-material/Send';
import HelpOutline from '@mui/icons-material/HelpOutline';
import PendingOutlined from '@mui/icons-material/PendingOutlined';
import Description from '@mui/icons-material/Description';
import client from '../../utils/httpClient';
import parseApiErrorMessage from '../../utils/parseApiErrorMessage';
import MessageRow from '../../components/MessageRow';
import ContentCopyIcon from '@mui/icons-material/ContentCopy';
import { OverlayTrigger, Tooltip } from 'react-bootstrap';

const Heading = styled.h1`
  background-image: linear-gradient(to right, #089fdf 21%, #5dd375 100%);
  height: 40px;
  color: #ffffff;
  font-weight: 500;
  font-size: 14px;
  padding-left: 20px;
  align-items: center;
  display: flex;
`;

const textBox = {
  width: '100%',
  height: '100%',
  marginTop: ' 20px',
  position: 'relative',
};
const chatBox = {
  background: '#eee6ff',
  padding: '20px 20px',
  width: '100%',
  height: 'calc(100vh - 190px)',
  overflowY: 'auto',
  borderRadius: '5px',
  marginTop: '20px',
};
// const input = {
//     borderRadius: '5px',
//     border: '2px solid #8c52ff',
//   }
const inputChat = {
  background: '#f7f7f7',
  padding: '10px',
  borderRadius: '7px',
  margin: '20px 10px',
};

const outputChat = {
  background: '#eaf4ff',
  padding: '10px',
  borderRadius: '7px',
  margin: '20px 10px',
  whiteSpace: 'pre-wrap',
};

const StyledTooltip = styled(Tooltip)`
  .tooltip-inner {
    max-width: 200px;
    padding: 0.25rem 0.5rem;
    color: white;
    text-align: center;
    background-color: #113ba4;
    border-radius: 0.25rem;
  }
`;

function CopyResourceAttribute({ value }) {
  const [isCopied, setIsCopied] = useState(false);
  const onCopy = async () => {
    await navigator.clipboard.writeText(value);
    setIsCopied(true);
    setTimeout(() => {
      setIsCopied(false);
    }, 2000);
  };

  return (
    <OverlayTrigger
      trigger="click"
      placement="top"
      overlay={<StyledTooltip id={value}>Copied !</StyledTooltip>}
      show={isCopied}
    >
      <>
        <ContentCopyIcon
          onClick={onCopy}
          style={{ marginTop: '2px', color: '#55ce7e', cursor: 'pointer' }}
        />
      </>
    </OverlayTrigger>
  );
}

const ChatPage = () => {
  const history = useHistory();
  const match = useRouteMatch();

  const [chats, setChats] = React.useState([]);
  const [loading, setLoading] = React.useState(false);
  const [error, setError] = React.useState(null);

  const handleSubmit = (values, actions) => {
    setLoading(true);
    client
      .post(`qanda/predictions`, values)
      .then((res) => {
        actions.setSubmitting(false);
        actions.resetForm();
        const previousChat = [...chats];
        previousChat.push({
          input: res.body?.input,
          output: res.body?.data?.choices[0]?.message?.content || '',
        });
        setChats([...previousChat]);
        setLoading(false);
      })
      .catch((error) => {
        actions.setSubmitting(false);
        setLoading(false);
        setError(parseApiErrorMessage(error));
      });
  };

  return (
    <Nesis>
      <Heading>
        <FileEarmarkPost size={25} color="white" className="mr-2" /> Chat with
        your Documents
      </Heading>
      <div style={{ padding: 8, marginLeft: 5 }}>
        <Container maxWidth="md">
          <Box sx={chatBox}>
            {error && <MessageRow variant="danger">{error}</MessageRow>}
            {chats.length > 0 ? (
              chats.map((chat) => (
                <>
                  <Box style={{ display: 'flex' }}>
                    <ChatBubbleIcon
                      style={{ marginTop: '20px', color: '#55ce7e' }}
                    />
                    <Box sx={inputChat}>
                      <Typography>{chat.input}</Typography>
                    </Box>
                  </Box>
                  <Box
                    style={{ display: 'flex', flexDirection: 'row-reverse' }}
                  >
                    <Box>
                      <ChatBubbleOutlineIcon
                        style={{ marginTop: '20px', color: '#55ce7e' }}
                      />
                      <CopyResourceAttribute value={chat.output} />
                    </Box>
                    <Box sx={outputChat}>
                      <Typography>{chat.output}</Typography>
                    </Box>
                  </Box>
                </>
              ))
            ) : (
              <>
                <Typography
                  sx={{ textAlign: 'center', marginTop: '50px' }}
                  variant="body1"
                  fontSize={'20px'}
                  fontWeight={'bold'}
                >
                  How can I help you
                  <IconButton>
                    <HelpOutline sx={{ width: '50px', height: '50px' }} />
                  </IconButton>
                </Typography>
              </>
            )}
            {loading && (
              <Typography
                sx={{ textAlign: 'center', marginTop: '50px' }}
                variant="body1"
                fontSize={'20px'}
                fontWeight={'bold'}
              >
                <LinearProgress />
              </Typography>
            )}
          </Box>
          <Box sx={textBox}>
            <Formik initialValues={{ query: '' }} onSubmit={handleSubmit}>
              {({ isSubmitting, resetForm, values }) => (
                <FormikForm>
                  <TextField
                    type="text"
                    id="query"
                    label=""
                    placeholder="Message..."
                    name="query"
                    disabled={isSubmitting}
                    postIcon={isSubmitting ? <PendingOutlined /> : <SendIcon />}
                  />
                </FormikForm>
              )}
            </Formik>
          </Box>
        </Container>
      </div>
    </Nesis>
  );
};

export default ChatPage;
