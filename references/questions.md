# Question bank

Ask only rows that matter for this person and haven't been answered, one per turn, roughly in this order: safety and scope → explanation and role (new reviews only) → devices → email, passwords and sign-in → recovery → accounts and optional areas → developer/admin → constraints. Most people need far fewer than all of them. "Ask if" means the fact hasn't been given yet, not that a "not sure" answer should be repeated.

Use each row's question and choices as written; you may adapt a label the person already gave you (for example "your Gmail" instead of "your main email"). The provider name or category is all you need: never addresses, account names, numbers, device serials or locations. Multi-select rows accept several answers; "None"/"No phone"-style answers exclude the others. No answer authorizes inspecting or changing anything.

## Safety and scope

| ID | Question | Choices | Why we ask | Ask if / what it changes |
| --- | --- | --- | --- | --- |
| S01 | Is there an immediate security or personal-safety concern? | No concern; Suspicious activity or lost access; Possible monitoring; Not sure | This tells us whether a routine review fits or safer support should come first. | First, unless already answered. Anything but "No concern" goes to the incident section. No details needed. |
| S02 | Whose accounts and devices are we reviewing? | My own; Helping with permission; Both; Not sure | This keeps the review within your authority. | Scope unknown. Clarify authority before any inspection or change. |
| S03 | How much explanation would you like? | Just the questions; Brief context; Step-by-step explanations | This lets me match the detail to you without changing the safety checks. | Only right after safety and scope at the start of a new review. Once the review is underway, skip it and match how they write. Never replace it with a "how thorough" question. |
| S04 | Do you develop software or administer systems? | Neither; Develop software; Administer systems; Both | This helps include relevant technical areas and skip irrelevant ones. | Early in a new review, or when technical topics come up. Once the review is underway, don't stop to ask it. Turns on the developer rows; not permission or a reason for jargon. |

## Devices

| ID | Question | Choices | Why we ask | Ask if / what it changes |
| --- | --- | --- | --- | --- |
| D01 multi | What phones do you use for these accounts? | iPhone; Android; Another type; No phone | Device compatibility affects which guidance and recovery options fit. | Unknown. No model or serial. |
| D02 multi | What computers do you use for these accounts? | Mac; Windows; Linux or another system; No computer | Cross-device use affects compatibility and independent access. | Unknown and relevant. |
| D03 | Are any devices managed by an employer or school? | None; Some; All; Not sure | Managed devices may have policies you can't change yourself. | Relevant. Managed changes go through their IT. |
| D04 | Are automatic security updates enabled? | All devices; Some devices; None; Not sure | This spots maintenance gaps without assuming a device needs replacing. | Personal devices in scope. Not sure isn't "off". |
| D05 | Do your devices use a screen lock? | All; Some; None; Not sure | Screen locks limit access if a device is lost or left unattended. | Unknown. Consider accessibility before suggesting changes. |
| D06 multi | Does anyone else use your devices or know their unlock codes? | Shared device use; Someone knows an unlock code; Neither; Not sure | Shared access changes the privacy and recovery assumptions we can make. | After safety. No names or codes; recheck safety if a concern appears. |
| D07 | Do you use browser extensions? | No; Yes; Not sure | Extensions can have access to your accounts or browsing. | Relevant. Having extensions isn't a finding by itself. |
| D08 | Is remote-access software installed on a personal device? | Yes; No; Not sure | Remote access may be intentional or worth a closer, separately agreed look. | Personal devices. Don't uninstall or assume compromise. |

## Email, passwords and sign-in

| ID | Question | Choices | Why we ask | Ask if / what it changes |
| --- | --- | --- | --- | --- |
| A01 | Which service runs your main email? | Gmail / Google; iCloud / Apple; Outlook / Microsoft; Another provider | Email usually recovers your other accounts; the provider name is enough. | Unknown. The service, not the mail app; don't guess from the phone brand. |
| A02 | Do you use a provider account to sign into other services? | Yes; No; Not sure | "Sign in with Google/Apple" makes several accounts depend on one. | Not yet known. |
| A03 multi | Which sign-in providers do you use? | Google; Apple; Microsoft; Another provider | This finds shared dependencies without listing every account. | A02 is Yes. |
| A04 | Do important accounts depend on an old email address or phone number you can't access? | Yes; No; Not sure | A dead recovery contact can lock you out even if sign-in works today. | Unknown. Yes raises recovery priority. |
| A05 multi | Where do you store passwords? | Password-manager app; Browser or built-in manager; Notes, documents or paper; Memory | This describes your current setup without assuming it needs replacing. | Unknown. No passwords, exports or screenshots. |
| A06 | Which password manager do you use? | Apple Passwords; Google Password Manager; 1Password; Another manager | Managers differ in compatibility and recovery options. | A manager is in use and the name matters. No vault access. |
| A07 | Do you reuse passwords across important accounts? | No; Some; Most; Not sure | Reuse lets one breach affect other accounts. | Unknown. No examples or account lists. |
| A08 | Do you need to share access with anyone? | No; Family or household; Work or team; Both | Sharing needs affect which options fit. | Relevant. Not a request to start sharing; no names. |
| A09 | Is 2FA enabled on your main email? | Yes; No; Not sure | This establishes your sign-in protection before discussing methods. | Not yet asked. A "not sure" answer completes it. |
| A10 multi | Which 2FA methods are enabled? | Authenticator app codes; SMS or phone-call codes; Approval prompts; Security keys | Methods differ in phishing resistance and recovery. | 2FA is on. Never ask for a code. |
| A11 | Do you use passkeys for important accounts? | Yes; No; Not sure | Passkeys change how sign-in and recovery work. | Separately from 2FA. A passkey isn't necessarily a physical key. |

## Recovery, backups and phone number

| ID | Question | Choices | Why we ask | Ask if / what it changes |
| --- | --- | --- | --- | --- |
| R01 | If your phone were unavailable, could you still get into your main email? | Yes; No; Not sure | This finds lockout risks before recommending changes. | Unknown. Ask about access, not codes or where things are kept. |
| R02 | Could you get into your password manager without your main device? | Yes; No; Not sure | Recovery shouldn't depend only on the device that's missing. | A manager exists. |
| R03 | Have you set up recovery methods for important accounts? | All; Some; None; Not sure | This shows where recovery needs attention before other changes. | Unknown. No account list. |
| R04 | Could you reach those recovery methods without the affected account or device? | Yes; Some; No; Not sure | Independent recovery prevents a lockout loop. | R03 isn't None. No locations or contents. |
| R05 | Is important data backed up separately from the original device? | All important data; Some; No; Not sure | A separate backup reduces loss if a device fails or is stolen. | Data matters. Sync alone isn't a backup. |
| R06 | Have you restored something from that backup? | Recently; Previously; Never; Not sure | A backup existing doesn't prove a restore works. | A backup exists. No restore during discovery. |
| R07 | Do important accounts use your phone number for sign-in or recovery? | Yes; No; Not sure | Losing or having your number taken affects those accounts. | Relevant. No number. |
| R08 | Have you turned on your carrier's account or number-transfer protections? | Yes; Some; No; Not sure | Carrier protections reduce unauthorized changes to your number. | R07 is Yes or otherwise relevant. No PIN. |

## Accounts and optional areas

| ID | Question | Choices | Why we ask | Ask if / what it changes |
| --- | --- | --- | --- | --- |
| C01 multi | Which kinds of accounts matter most to you? | Financial services; Work or business; Health or government; Other important accounts | This sets priorities without collecting your account list. | Unknown. No institutions or balances. |
| C02 | Do apps, integrations or AI tools have access to your accounts or files? | Yes; No; Not sure | Connected services can keep access separately from your sign-in. | Unknown. No inspection yet. |
| C03 | Do you share account access, files or location with others? | Yes; No; Not sure | Existing sharing changes which privacy questions matter. | After safety. No names; nothing revoked automatically. |
| C04 | Are there old accounts or subscriptions you no longer use? | Yes; No; Not sure | Unused accounts can still hold data, recovery links or billing. | Relevant. Nothing deleted during discovery. |
| C05 multi | Which of these also apply? | Home Wi-Fi or smart devices; Domains or websites; Cryptocurrency; Emergency access planning | This turns on optional areas only where they fit. | "None" can be typed. Never collect seeds, addresses or Wi-Fi passwords. |
| C06 | Would you like country-specific identity and fraud guidance? | Yes; Universal guidance only; Decide later | Local protections vary, but the core review doesn't need your country. | Not already declined. On Yes, ask the country directly as free text, and say they can skip it and still get the universal guidance. |
| C07 | Have you received suspicious security or support messages? | No; Yes, unsure about them; Yes, recognized as suspicious; Not sure | This decides whether scam-spotting guidance would help. | Relevant. No message uploads; active loss or fraud goes to incidents. |

## Developer and administrator (only if S04 says so)

| ID | Question | Choices | Why we ask | Ask if / what it changes |
| --- | --- | --- | --- | --- |
| T01 multi | Which systems do you manage? | Repositories or package publishing; Cloud or deployments; DNS or email administration; Other infrastructure | These systems carry different credentials and recovery dependencies. | Developer/admin. No company or project names. |
| T02 multi | Where are development secrets managed? | Secret manager; CI/CD or hosting configuration; Local environment files; Other approach | This shows how secrets are stored without looking at them. | They manage secrets. No paths or values. |
| T03 | Are development and production credentials separated? | Yes; Partly; No; Not applicable | Separation limits the reach of an accidental leak. | Both environments exist. |
| T04 | Have you reviewed tokens, SSH keys and service-account access? | Recently; Previously; Never; Not sure | Old access can outlive the task or person it was made for. | Relevant. No enumeration without separate agreement. |
| T05 | Is independent recovery available for critical admin accounts? | All; Some; None; Not sure | Admin lockout affects everyone depending on those systems. | Admin scope. |

## Constraints and priorities

| ID | Question | Choices | Why we ask | Ask if / what it changes |
| --- | --- | --- | --- | --- |
| P01 | What budget should recommendations assume? | Free only; Paid if worthwhile; No preference yet | Recommendations should be practical without assuming a purchase. | Before the assessment, if not already said. Not payment consent. |
| P02 | How much change would you consider? | Keep existing tools; Small changes; Open to larger changes | This helps compare realistic paths. | Before offering paths. |
| P03 multi | What matters most to you? | Preventing account takeover; Avoiding lockout or data loss; Privacy or unwanted access; Simplicity | Priorities explain why one path fits better than another. | Goals unknown. |
| P04 multi | Should recommendations account for any practical constraints? | Accessibility needs; Shared devices or limited connectivity; Another constraint; None | This makes suggestions usable, not just technically possible. | Optional. A short note is enough; never a diagnosis. |
