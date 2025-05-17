// Import Libraries
import { validateUserCookiesFromSSR } from '../../utils/userVerification'

// Import Components
import Board from '../../components/Board'
import Sidebar from '../../components/Sidebar'

// Import Styles
import styles from './AboutUs.module.scss'

// About Us Page
const AboutUsPage = () => {
  // Render the page.
  return (
    <div className={styles.dashboard}>
      <div className={styles.sidebar}>
        <Sidebar />
      </div>

      <div className={styles.page}>
        <Board heading="About Us" />

        <div className={styles.content + ' card shadow-sm col display-4'}>
          <h3>ITAF IRCTC</h3>
          <h6>
            We are ITAF (IT-Anti Fraud) team, IRCTC. We perform cyber space
            surveillance and pro-active analysis in coordination with Railways
            vigilance and Railways Protection Force, cyber crime police and
            other investigating agencies.
            <ul>
              <li>
                We are utilising state of the art technological means to prevent
                the booking of tickets through illegal means (such as bots) and
                resale of tickets at inflated prices through unauthorized
                software.
              </li>
              <li>
                We track and analyze mentions of IRCTC to gain insights on the
                strategies being implemented by the touts to abuse IRCTC
                infrastructure.
              </li>
              <li>
                We monitor various channels on the surface web such as social
                media, forums and news sites for mentions of IRCTC to understand
                the new touting methodologies and modes.
              </li>
              <li>
                We also track deep and dark web forums to identify leaks in
                regards to the source code, data, PII of executives and
                third-party sale of IRCTC user IDs and other services.
              </li>
              <li>
                We flag suspicious users in regards to the user's meta details
                and booking behaviour to ensure the platform stays fair and safe
                for railway passengers.
              </li>
            </ul>
          </h6>
          <h6>
            Our goal is to make tickets available at fair prices to the general
            public. This is centered around preventing touts from taking
            advantage of the demand for the most frequented routes and trains.
          </h6>
        </div>
      </div>
    </div>
  )
}

export default AboutUsPage

export async function getServerSideProps({ req, res }) {
  return validateUserCookiesFromSSR(req, res)
}
